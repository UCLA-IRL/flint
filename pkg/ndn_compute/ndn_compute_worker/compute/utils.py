from ndn.encoding import FormalName, Component

class DeserializedTransformationInterest:
    def __init__(self):
        self.app = ""
        self.filepath = ""
        self.transformations = []
        self.shard = None

    def set_app(self, appname: str):
        self.app = appname

    def set_file_path(self, filepath: str):
        self.filepath = filepath

    def set_transformations(self, transformations: list[str]):
        self.transformations = transformations

    def set_shard(self, shard: int):
        self.shard = shard

    def __repr__(self) -> str:
        return f"<{self.filepath}, {self.shard}, {self.transformations}>"
    
    def __str__(self) -> str:
        return self.__repr__()
    
    @staticmethod
    def decode(name: FormalName):
        result = DeserializedTransformationInterest()

        file_path = []
        transformations = []
        done_with_path = False
        processing_transformations = False

        for idx, component in enumerate(map(lambda c: bytes(Component.get_value(c)).decode("utf-8"), name)):
            if idx == 0:
                result.set_app(component)
            if idx == 1:
                continue # who cares
            if not done_with_path and component == "LINEAGE": # LINEAGE spotted, done with path and shard is the last one we saw
                result.set_shard(int(file_path.pop()))
                result.set_file_path("/".join(file_path))
                done_with_path = True
            elif not done_with_path: # add this to path
                file_path.append(component)
            elif component == "TRANSFORMATIONS": # done with path and shard
                processing_transformations = True
            elif processing_transformations and component == "END":
                processing_transformations = False
                result.set_transformations(transformations)
            else:
                transformations.append(component)
        return result
