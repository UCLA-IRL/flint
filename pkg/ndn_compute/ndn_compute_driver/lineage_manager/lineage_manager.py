from typing import Optional, Self


class LineageManager:
    """
    Keeps track of transformation lineage for distributed datasets (files).

    The Lineage Manager keeps track of multiple paths (files). Each file has its own tree.
    """
    class _TransformationNode:
        def __init__(self, transformation: Optional[str]):
            self.transformation: Optional[str] = transformation
            # self.parent: Optional[Self] = parent
            self.children: list[Self] = []
            self.materialized = False

    def __init__(self):
        self._lineage_trees: dict[str, LineageManager._TransformationNode] = dict()

    def add_transformations(self, path: str, transformations: list[str]) -> None:
        """
        Add vertices and edges as necessary to reflect a series of transformations the user may materialize in the
        future for a certain path (file).

        :param path: The path (file) the transformations apply to
        :param transformations: The ordered list of transformations the user will want to do in the future
        """
        if path not in self._lineage_trees:
            self._lineage_trees[path] = LineageManager._TransformationNode(None)

        cur = self._lineage_trees[path]
        for transformation in transformations:
            child_found = False

            for child in cur.children:
                if child.transformation is not None and child.transformation == transformation:
                    cur = child
                    child_found = True
                    break

            if not child_found:
                child = LineageManager._TransformationNode(transformation)
                cur.children.append(child)
                cur = child

    def materialize_transformations(self, path: str, transformations: list[str]) -> list[list[str]]:
        """
        Express desire to materialize a series of transformations for a certain path (file).

        :param path: The path (file) the transformations apply to
        :param transformations: The ordered list of transformations the user wants to materialize
        :return: An ordered list of lists, where each inner list is a prefix of the provided transformations, in the
                 order they should be materialized. Each inner list should be materialized because other transformations
                 depend on it.
        """
        # do a pass over the tree and add any transformations
        # (this should be fast as the tree should not be very big)
        self.add_transformations(path, transformations)

        result = []

        cur = self._lineage_trees[path]
        prefix = []
        for i, transformation in enumerate(transformations):
            next_transformation = transformations[i + 1] if i + 1 < len(transformations) else None

            prefix.append(transformation)

            for child in cur.children:
                if child.transformation is not None and child.transformation == transformation:
                    cur = child

                    # do not materialize a prefix if it has already been materialized
                    if cur.materialized:
                        break

                    # do not materialize a prefix if it is the last one in the path (it is added later)
                    if next_transformation is None:
                        break

                    # do not materialize a prefix if it has less than one child
                    if len(cur.children) < 2:
                        break

                    # do not materialize a prefix if all its children (excluding the child on the path)
                    # are materialized
                    if all([
                        child.materialized or child.transformation == next_transformation
                        for child in cur.children
                    ]):
                        break

                    # otherwise, materialize the prefix
                    cur.materialized = True
                    result.append(list(prefix))
                    break

        cur.materialized = True
        result.append(list(prefix))

        return result
