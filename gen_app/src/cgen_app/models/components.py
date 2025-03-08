from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Component:
    name: str
    type: str
    description: str
    requirements: str = ""
    dependencies: List[str] = field(default_factory=list)
    tests_required: bool = True
    priority: int = 0
    verification_criteria: List[str] = field(default_factory=list)
    generated_code: str = ""
    validated: bool = False


@dataclass
class File:
    path: str
    components: List[Component]
    description: str = ""
    imports: List[str] = field(default_factory=list)
    generated_code: str = ""
    is_entrypoint: bool = False


@dataclass
class Structure:
    structure: Dict[str, Any]
    files: List[File]

    @classmethod
    def from_dict(cls, data: Dict) -> "Structure":
        files = []
        for file_data in data.get("files", []):
            components = [
                Component(**comp_data) for comp_data in file_data.get("components", [])
            ]
            files.append(
                File(
                    path=file_data["path"],
                    components=components,
                    description=file_data.get("description", ""),
                    imports=file_data.get("imports", []),
                    is_entrypoint=file_data.get("is_entrypoint", False),
                )
            )
        return cls(structure=data.get("structure", {}), files=files)
