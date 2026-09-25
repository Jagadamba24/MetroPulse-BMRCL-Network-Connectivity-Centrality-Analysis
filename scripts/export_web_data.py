"""
Exports the Bangalore Metro network analysis data as a standalone JavaScript module (bangalore_metro_data.js)
so the web application can run seamlessly both locally and over HTTP without CORS issues.
"""

import json
import pandas as pd

nodes_df = pd.read_csv("data/bangalore_metro_nodes.csv")
edges_df = pd.read_csv("data/bangalore_metro_edges.csv")
cent_df = pd.read_csv("data/bangalore_metro_centrality.csv")
sim_df = pd.read_csv("data/bangalore_station_similarity.csv") if pd.io.common.file_exists("data/bangalore_station_similarity.csv") else pd.DataFrame()

with open("data/bangalore_metro_analysis.json", "r") as f:
    analysis_json = json.load(f)

# Merge centrality metrics into nodes list
nodes_data = []
cent_dict = cent_df.set_index("station").to_dict(orient="index")

for _, r in nodes_df.iterrows():
    st = r["id"]
    c = cent_dict.get(st, {})
    nodes_data.append({
        "id": st,
        "name": r["name"],
        "lat": float(r["latitude"]),
        "lon": float(r["longitude"]),
        "zone": r["zone"],
        "lines": r["lines"].split("; "),
        "corridors": r["corridors"].split("; "),
        "line_count": int(r["line_count"]),
        "is_interchange": bool(r["is_interchange"]),
        "footfall_tier": r["footfall_tier"],
        "is_phase1": bool(r["is_phase1_operational"]),
        "degree": int(c.get("degree", 2)),
        "degree_centrality": float(c.get("degree_centrality", 0.024)),
        "closeness_centrality": float(c.get("closeness_centrality", 0.05)),
        "betweenness_centrality": float(c.get("betweenness_centrality", 0.0)),
        "betweenness_phase1": float(c.get("betweenness_phase1", 0.0)),
        "eigenvector_centrality": float(c.get("eigenvector_centrality", 0.0)),
        "pagerank": float(c.get("pagerank", 0.012)),
        "clustering_coefficient": float(c.get("clustering_coefficient", 0.0)),
        "is_articulation_point": bool(c.get("is_articulation_point", True))
    })

edges_data = []
for _, r in edges_df.iterrows():
    edges_data.append({
        "source": r["source"],
        "target": r["target"],
        "line": r["line"],
        "color": r["line_color"],
        "dist_km": float(r["distance_km"]),
        "time_min": float(r["time_min"]),
        "status": r["status"]
    })

sim_data = []
if not sim_df.empty:
    for _, r in sim_df.head(25).iterrows():
        sim_data.append({
            "st1": r["station_1"],
            "st2": r["station_2"],
            "shared": eval(r["shared_neighbors"]) if isinstance(r["shared_neighbors"], str) else r["shared_neighbors"],
            "jaccard": float(r["jaccard_similarity"])
        })

js_content = f"""// Auto-generated Bangalore Namma Metro Network Dataset
window.METRO_DATA = {{
    nodes: {json.dumps(nodes_data, indent=2)},
    edges: {json.dumps(edges_data, indent=2)},
    similarity: {json.dumps(sim_data, indent=2)},
    analysis: {json.dumps(analysis_json, indent=2)}
}};
"""

with open("bangalore_metro_data.js", "w", encoding="utf-8") as f:
    f.write(js_content)

print(f"Exported bangalore_metro_data.js with {len(nodes_data)} stations and {len(edges_data)} track edges.")
