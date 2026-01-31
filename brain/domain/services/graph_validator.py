from typing import List, Dict, Set, Deque
from collections import deque
from brain.domain.entities.knowledge_node import KnowledgeNode

class GraphValidationError(Exception):
    """Custom exception for graph-related errors."""
    pass

class KnowledgeGraphValidator:
    @staticmethod
    def get_topological_order(nodes: List[KnowledgeNode]) -> List[KnowledgeNode]:
        """
        Performs a topological sort on a list of KnowledgeNode objects using Kahn's algorithm.
        This not only provides the correct learning sequence but also detects cycles.

        Args:
            nodes: A list of KnowledgeNode domain entities.

        Returns:
            A list of KnowledgeNode objects in topological order.

        Raises:
            GraphValidationError: If the graph contains a cycle.
        """
        # 1. Build in-degree map and adjacency list
        in_degree: Dict[str, int] = {node.id: 0 for node in nodes}
        adj: Dict[str, List[str]] = {node.id: [] for node in nodes}
        node_map: Dict[str, KnowledgeNode] = {node.id: node for node in nodes}

        for node in nodes:
            # For each dependency (parent) of the current node
            for parent_dep in node.dependencies:
                if parent_dep.id in adj:
                    # The current node is a child of parent_dep
                    adj[parent_dep.id].append(node.id)
                    # Increment the in-degree of the child node
                    in_degree[node.id] += 1

        # 2. Initialize queue with nodes having an in-degree of 0
        queue: Deque[str] = deque(
            [node_id for node_id, degree in in_degree.items() if degree == 0]
        )
        
        topo_order: List[KnowledgeNode] = []

        # 3. Process the graph
        while queue:
            u_id = queue.popleft()
            if u_id in node_map:
                topo_order.append(node_map[u_id])

            # For each neighbor of the current node, reduce its in-degree
            for v_id in adj.get(u_id, []):
                in_degree[v_id] -= 1
                # If in-degree becomes 0, add it to the queue
                if in_degree[v_id] == 0:
                    queue.append(v_id)

        # 4. Check for cycles
        if len(topo_order) != len(nodes):
            # If the number of nodes in the sorted order is not equal to the
            # total number of nodes, the graph has a cycle.
            raise GraphValidationError(
                "Cycle detected! The curriculum has circular dependencies that cannot be resolved."
            )

        return topo_order
