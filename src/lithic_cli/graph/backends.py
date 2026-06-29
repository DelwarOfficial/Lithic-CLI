"""Graph storage backends for persistent graph data."""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

_log = logging.getLogger("lithic_cli.graph.backends")


class GraphBackend(ABC):
    """Abstract graph storage backend."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to backend storage."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from backend storage.""" 
        pass
    
    @abstractmethod
    def store_graph(self, graph_data: dict[str, Any], project_id: str) -> bool:
        """Store complete graph data."""
        pass
    
    @abstractmethod
    def load_graph(self, project_id: str) -> dict[str, Any] | None:
        """Load complete graph data."""
        pass
    
    @abstractmethod
    def update_nodes(self, nodes: list[dict[str, Any]], project_id: str) -> bool:
        """Update specific nodes in graph."""
        pass
    
    @abstractmethod
    def update_edges(self, edges: list[dict[str, Any]], project_id: str) -> bool:
        """Update specific edges in graph."""
        pass
    
    @abstractmethod
    def query_nodes(self, filters: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
        """Query nodes by filters."""
        pass
    
    @abstractmethod
    def query_edges(self, filters: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
        """Query edges by filters."""
        pass
    
    @abstractmethod
    def find_paths(self, source: str, target: str, project_id: str, max_depth: int = 6) -> list[list[str]]:
        """Find paths between nodes."""
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str, project_id: str, direction: str = "both") -> list[str]:
        """Get neighboring nodes."""
        pass
    
    @abstractmethod
    def get_stats(self, project_id: str) -> dict[str, Any]:
        """Get graph statistics."""
        pass
    
    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Check backend health."""
        pass


class FileSystemBackend(GraphBackend):
    """File system based graph storage."""
    
    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or Path.cwd() / ".lithic" / "graphs"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to file system storage."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self._connected = True
            _log.info(f"Connected to file system backend at {self.storage_dir}")
            return True
        except Exception as e:
            _log.error(f"Failed to connect to file system: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from file system."""
        self._connected = False
        return True
    
    def _get_project_path(self, project_id: str) -> Path:
        """Get project storage path."""
        return self.storage_dir / f"{project_id}.json"
    
    def store_graph(self, graph_data: dict[str, Any], project_id: str) -> bool:
        """Store complete graph data to JSON file."""
        if not self._connected:
            return False
        
        try:
            project_path = self._get_project_path(project_id)
            with project_path.open('w') as f:
                json.dump(graph_data, f, indent=2)
            _log.info(f"Stored graph for project {project_id}")
            return True
        except Exception as e:
            _log.error(f"Failed to store graph: {e}")
            return False
    
    def load_graph(self, project_id: str) -> dict[str, Any] | None:
        """Load complete graph data from JSON file."""
        if not self._connected:
            return None
        
        try:
            project_path = self._get_project_path(project_id)
            if not project_path.exists():
                return None
            
            with project_path.open('r') as f:
                return json.load(f)
        except Exception as e:
            _log.error(f"Failed to load graph: {e}")
            return None
    
    def update_nodes(self, nodes: list[dict[str, Any]], project_id: str) -> bool:
        """Update nodes in existing graph."""
        graph_data = self.load_graph(project_id)
        if not graph_data:
            graph_data = {"nodes": {}, "edges": {}}
        
        # Update nodes
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                graph_data["nodes"][node_id] = node
        
        return self.store_graph(graph_data, project_id)
    
    def update_edges(self, edges: list[dict[str, Any]], project_id: str) -> bool:
        """Update edges in existing graph."""
        graph_data = self.load_graph(project_id)
        if not graph_data:
            graph_data = {"nodes": {}, "edges": {}}
        
        # Update edges
        for edge in edges:
            edge_id = edge.get("id") or f"{edge.get('source')}->{edge.get('target')}"
            graph_data["edges"][edge_id] = edge
        
        return self.store_graph(graph_data, project_id)
    
    def query_nodes(self, filters: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
        """Query nodes by simple filters."""
        graph_data = self.load_graph(project_id)
        if not graph_data:
            return []
        
        nodes = graph_data.get("nodes", {}).values()
        results = []
        
        for node in nodes:
            match = True
            for key, value in filters.items():
                if key not in node or node[key] != value:
                    match = False
                    break
            if match:
                results.append(node)
        
        return results
    
    def query_edges(self, filters: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
        """Query edges by simple filters."""
        graph_data = self.load_graph(project_id)
        if not graph_data:
            return []
        
        edges = graph_data.get("edges", {}).values()
        results = []
        
        for edge in edges:
            match = True
            for key, value in filters.items():
                if key not in edge or edge[key] != value:
                    match = False
                    break
            if match:
                results.append(edge)
        
        return results
    
    def find_paths(self, source: str, target: str, project_id: str, max_depth: int = 6) -> list[list[str]]:
        """Find paths using simple BFS."""
        graph_data = self.load_graph(project_id)
        if not graph_data:
            return []
        
        # Build adjacency list
        adj_list = {}
        for edge in graph_data.get("edges", {}).values():
            src = edge.get("source")
            tgt = edge.get("target")
            if src and tgt:
                if src not in adj_list:
                    adj_list[src] = []
                adj_list[src].append(tgt)
        
        # BFS to find paths
        queue = [[source]]
        paths = []
        
        while queue and len(paths) < 10:  # Limit results
            path = queue.pop(0)
            node = path[-1]
            
            if len(path) > max_depth:
                continue
            
            if node == target:
                paths.append(path)
                continue
            
            for neighbor in adj_list.get(node, []):
                if neighbor not in path:  # Avoid cycles
                    queue.append(path + [neighbor])
        
        return paths
    
    def get_neighbors(self, node_id: str, project_id: str, direction: str = "both") -> list[str]:
        """Get neighboring nodes."""
        graph_data = self.load_graph(project_id)
        if not graph_data:
            return []
        
        neighbors = set()
        
        for edge in graph_data.get("edges", {}).values():
            src = edge.get("source")
            tgt = edge.get("target")
            
            if direction in ["out", "both"] and src == node_id:
                neighbors.add(tgt)
            if direction in ["in", "both"] and tgt == node_id:
                neighbors.add(src)
        
        return list(neighbors)
    
    def get_stats(self, project_id: str) -> dict[str, Any]:
        """Get graph statistics."""
        graph_data = self.load_graph(project_id)
        if not graph_data:
            return {"nodes": 0, "edges": 0}
        
        return {
            "nodes": len(graph_data.get("nodes", {})),
            "edges": len(graph_data.get("edges", {})),
            "storage_size_mb": self._get_project_path(project_id).stat().st_size / (1024 * 1024)
        }
    
    def health_check(self) -> dict[str, Any]:
        """Check file system health."""
        return {
            "healthy": self._connected and self.storage_dir.exists(),
            "backend": "filesystem",
            "storage_dir": str(self.storage_dir),
            "connected": self._connected
        }


class PostgreSQLBackend(GraphBackend):
    """PostgreSQL backend for graph storage."""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv(
            "LITHIC_POSTGRES_URL", "postgresql://localhost/lithic_graphs"
        )
        self._connection = None
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to PostgreSQL."""
        try:
            import psycopg2
            self._connection = psycopg2.connect(self.connection_string)
            self._connected = True
            self._setup_tables()
            _log.info("Connected to PostgreSQL backend")
            return True
        except ImportError:
            _log.warning("psycopg2 not installed, PostgreSQL backend unavailable")
            return False
        except Exception as e:
            _log.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from PostgreSQL."""
        if self._connection:
            self._connection.close()
            self._connected = False
        return True
    
    def _setup_tables(self) -> None:
        """Create tables if they don't exist."""
        with self._connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graph_nodes (
                    project_id VARCHAR(255),
                    node_id VARCHAR(255),
                    node_type VARCHAR(100),
                    properties JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (project_id, node_id)
                );
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graph_edges (
                    project_id VARCHAR(255),
                    edge_id VARCHAR(255),
                    source_id VARCHAR(255),
                    target_id VARCHAR(255),
                    edge_type VARCHAR(100),
                    properties JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (project_id, edge_id)
                );
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_project ON graph_nodes(project_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_project ON graph_edges(project_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_id);")
            
        self._connection.commit()
    
    def store_graph(self, graph_data: dict[str, Any], project_id: str) -> bool:
        """Store complete graph data."""
        if not self._connected:
            return False
        
        try:
            with self._connection.cursor() as cursor:
                # Clear existing data
                cursor.execute("DELETE FROM graph_nodes WHERE project_id = %s", (project_id,))
                cursor.execute("DELETE FROM graph_edges WHERE project_id = %s", (project_id,))
                
                # Insert nodes
                for node_id, node_data in graph_data.get("nodes", {}).items():
                    cursor.execute("""
                        INSERT INTO graph_nodes (project_id, node_id, node_type, properties)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        project_id,
                        node_id,
                        node_data.get("type", "unknown"),
                        json.dumps(node_data)
                    ))
                
                # Insert edges
                for edge_id, edge_data in graph_data.get("edges", {}).items():
                    cursor.execute("""
                        INSERT INTO graph_edges (project_id, edge_id, source_id, target_id, edge_type, properties)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        project_id,
                        edge_id,
                        edge_data.get("source"),
                        edge_data.get("target"),
                        edge_data.get("type", "unknown"),
                        json.dumps(edge_data)
                    ))
            
            self._connection.commit()
            _log.info(f"Stored graph for project {project_id} in PostgreSQL")
            return True
            
        except Exception as e:
            _log.error(f"Failed to store graph in PostgreSQL: {e}")
            self._connection.rollback()
            return False
    
    def load_graph(self, project_id: str) -> dict[str, Any] | None:
        """Load complete graph data."""
        if not self._connected:
            return None
        
        try:
            graph_data = {"nodes": {}, "edges": {}}
            
            with self._connection.cursor() as cursor:
                # Load nodes
                cursor.execute(
                    "SELECT node_id, properties FROM graph_nodes WHERE project_id = %s",
                    (project_id,)
                )
                for node_id, properties in cursor.fetchall():
                    graph_data["nodes"][node_id] = json.loads(properties)
                
                # Load edges  
                cursor.execute(
                    "SELECT edge_id, properties FROM graph_edges WHERE project_id = %s",
                    (project_id,)
                )
                for edge_id, properties in cursor.fetchall():
                    graph_data["edges"][edge_id] = json.loads(properties)
            
            return graph_data if graph_data["nodes"] or graph_data["edges"] else None
            
        except Exception as e:
            _log.error(f"Failed to load graph from PostgreSQL: {e}")
            return None
    
    def find_paths(self, source: str, target: str, project_id: str, max_depth: int = 6) -> list[list[str]]:
        """Find paths using PostgreSQL recursive CTE."""
        if not self._connected:
            return []
        
        try:
            with self._connection.cursor() as cursor:
                cursor.execute("""
                    WITH RECURSIVE paths(node, path, depth) AS (
                        SELECT source_id, ARRAY[source_id], 1
                        FROM graph_edges 
                        WHERE project_id = %s AND source_id = %s
                        
                        UNION ALL
                        
                        SELECT e.target_id, p.path || e.target_id, p.depth + 1
                        FROM graph_edges e
                        JOIN paths p ON e.source_id = p.node
                        WHERE e.project_id = %s 
                          AND p.depth < %s
                          AND NOT (e.target_id = ANY(p.path))
                    )
                    SELECT path FROM paths 
                    WHERE node = %s
                    LIMIT 10
                """, (project_id, source, project_id, max_depth, target))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            _log.error(f"Failed to find paths in PostgreSQL: {e}")
            return []
    
    def get_stats(self, project_id: str) -> dict[str, Any]:
        """Get graph statistics."""
        if not self._connected:
            return {}
        
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM graph_nodes WHERE project_id = %s",
                    (project_id,)
                )
                node_count = cursor.fetchone()[0]
                
                cursor.execute(
                    "SELECT COUNT(*) FROM graph_edges WHERE project_id = %s", 
                    (project_id,)
                )
                edge_count = cursor.fetchone()[0]
                
                return {"nodes": node_count, "edges": edge_count}
                
        except Exception as e:
            _log.error(f"Failed to get stats from PostgreSQL: {e}")
            return {}
    
    def update_nodes(self, nodes: list[dict[str, Any]], project_id: str) -> bool:
        """Update specific nodes."""
        # Implementation similar to store_graph but for updates only
        return False  # Simplified for now
    
    def update_edges(self, edges: list[dict[str, Any]], project_id: str) -> bool:
        """Update specific edges."""
        return False  # Simplified for now
    
    def query_nodes(self, filters: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
        """Query nodes with filters."""
        return []  # Simplified for now
    
    def query_edges(self, filters: dict[str, Any], project_id: str) -> list[dict[str, Any]]:
        """Query edges with filters."""
        return []  # Simplified for now
    
    def get_neighbors(self, node_id: str, project_id: str, direction: str = "both") -> list[str]:
        """Get neighboring nodes."""
        return []  # Simplified for now
    
    def health_check(self) -> dict[str, Any]:
        """Check PostgreSQL health."""
        if not self._connected:
            return {"healthy": False, "backend": "postgresql", "error": "Not connected"}
        
        try:
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {"healthy": True, "backend": "postgresql"}
        except Exception as e:
            return {"healthy": False, "backend": "postgresql", "error": str(e)}


def create_backend(backend_type: str = "filesystem", **kwargs) -> GraphBackend:
    """Create graph backend instance."""
    if backend_type == "filesystem":
        return FileSystemBackend(kwargs.get("storage_dir"))
    elif backend_type == "postgresql":
        return PostgreSQLBackend(kwargs.get("connection_string"))
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")


def get_default_backend(storage_dir: Path | None = None) -> GraphBackend:
    """Get default graph backend based on environment."""
    backend_type = os.getenv("LITHIC_GRAPH_BACKEND", "filesystem")
    
    try:
        backend = create_backend(backend_type, storage_dir=storage_dir)
        if backend.connect():
            return backend
    except Exception as e:
        _log.warning(f"Failed to create {backend_type} backend: {e}")
    
    # Fallback to filesystem
    filesystem_backend = FileSystemBackend(storage_dir)
    filesystem_backend.connect()
    return filesystem_backend