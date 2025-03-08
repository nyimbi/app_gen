import networkx as nx
from typing import List, Tuple
from models.components import Structure, Component
from core.exceptions import DependencyError
import logging

logger = logging.getLogger("appgen")


class DependencyResolver:
    @staticmethod
    def create_dependency_graph(structure: Structure) -> nx.DiGraph:
        G = nx.DiGraph()
        component_map = {}
        for file in structure.files:
            for component in file.components:
                component_id = f"{file.path}:{component.name}"
                component_map[component.name] = component_id
                G.add_node(
                    component_id,
                    component=component,
                    file_path=file.path,
                    priority=component.priority,
                )
        for file in structure.files:
            for component in file.components:
                component_id = f"{file.path}:{component.name}"
                for dep_name in component.dependencies:
                    if dep_name in component_map:
                        G.add_edge(component_map[dep_name], component_id)
                    else:
                        logger.warning(
                            f"Dependency '{dep_name}' not found for component '{component.name}'"
                        )
        return G

    @staticmethod
    def get_generation_order(structure: Structure) -> List[Tuple[str, Component]]:
        G = DependencyResolver.create_dependency_graph(structure)
        cycles = list(nx.simple_cycles(G))
        if cycles:
            raise DependencyError(
                f"Circular dependencies detected: {', '.join(' -> '.join(c) for c in cycles)}"
            )
        topo_order = list(
            nx.lexicographical_topological_sort(
                G, key=lambda n: (-G.nodes[n].get("priority", 0), n)
            )
        )
        return [
            (G.nodes[comp_id]["file_path"], G.nodes[comp_id]["component"])
            for comp_id in topo_order
        ]
