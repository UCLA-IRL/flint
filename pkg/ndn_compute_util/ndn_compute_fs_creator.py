import random
from typing import List, Set
from pathlib import Path


def create_fs_from_directory(in_dir: str, out_dir: str,
                             num_partitions: int = 2, num_copies: int = 1,
                             chunk_size: int = 64) -> None:
    """Create chunked files to be used in a toy distributed filesystem.
    The procedure works as follows:

    1. Create folders in `out_dir` labeled 1 to `num_partitions`
    2. Mirror the structure of `in_dir` into every "`out_dir`/<num>" folder, where every
      file in `in_dir` is an empty directory of the same name in "`out_dir`/<num>".
    3. Chunk the files in `in_dir` into chunks of approximately `chunk_size` megabytes (note that
      the directory structure within `in_dir` is preserved, but `in_dir` itself is not included.
      Note that chunked file boundaries should be along newlines in the original file.
    4. For every chunk, choose at random which `num_copies` partitions to which to put the chunk in,
      then move the chunk to the folder whose name corresponds to the original file. The
      chunk will be named "i" where i is the 0-indexed order of the chunk.

    Precondition:
    - `num_copies` <= `num_partitions`
    - `in_dir`, `out_dir`, exist as directories on the filesystem
    - `out_dir` should be empty
    - all files in in_dir are text files
    """
    in_path = Path(in_dir)
    out_path = Path(out_dir)

    # Validate preconditions
    if not in_path.is_dir() or not out_path.is_dir():
        raise ValueError("Input and output directories must exist")
    if len(list(out_path.iterdir())) > 0:
        raise ValueError("Output directory must be empty")
    if num_copies > num_partitions:
        raise ValueError("Number of copies cannot exceed number of partitions")

    # Create partition directories
    partition_dirs = []
    for i in range(1, num_partitions + 1):
        partition_dir = out_path / str(i)
        partition_dir.mkdir()
        partition_dirs.append(partition_dir)

    def should_process_path(path: Path) -> bool:
        """Check if a path should be processed (not hidden)."""
        return not any(part.startswith('.') for part in path.parts)

    def create_mirror_structure(source_dir: Path, dest_dirs: List[Path]) -> None:
        """Mirror the directory structure from source to all destination directories."""
        for item in source_dir.rglob("*"):
            if not should_process_path(item.relative_to(source_dir)):
                continue

            if item.is_file():
                # Create a directory with the file's name in each partition
                rel_path = item.relative_to(source_dir)
                for dest_dir in dest_dirs:
                    # Create parent directories
                    file_dir = dest_dir / rel_path
                    file_dir.mkdir(parents=True, exist_ok=True)

    def chunk_file(file_path: Path, chunk_size_mb: int) -> List[str]:
        """Split a file into chunks of approximately chunk_size_mb, respecting newlines."""
        chunk_size_bytes = chunk_size_mb * 1024 * 1024
        chunks = []
        current_chunk = []
        current_size = 0

        print(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_size = len(line.encode('utf-8'))
                if current_size + line_size > chunk_size_bytes and current_chunk:
                    chunks.append(''.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                current_chunk.append(line)
                current_size += line_size

            if current_chunk:
                chunks.append(''.join(current_chunk))

        return chunks

    def select_random_partitions(num_partitions: int, num_copies: int) -> Set[int]:
        """Select num_copies random partition numbers from 1 to num_partitions."""
        return set(random.sample(range(1, num_partitions + 1), num_copies))

    # Step 1 & 2: Create partition directories and mirror structure
    create_mirror_structure(in_path, partition_dirs)

    # Step 3 & 4: Process each file
    for file_path in in_path.rglob("*"):
        if not should_process_path(file_path.relative_to(in_path)):
            continue

        if file_path.is_file():
            rel_path = file_path.relative_to(in_path)
            chunks = chunk_file(file_path, chunk_size)

            # Process each chunk
            for chunk_idx, chunk_content in enumerate(chunks):
                # Select random partitions for this chunk
                selected_partitions = select_random_partitions(num_partitions, num_copies)

                # Write chunk to selected partitions inside the file's directory
                for partition_num in selected_partitions:
                    partition_dir = out_path / str(partition_num)
                    chunk_dir = partition_dir / rel_path
                    chunk_path = chunk_dir / str(chunk_idx)

                    with open(chunk_path, 'w', encoding='utf-8') as f:
                        f.write(chunk_content)
