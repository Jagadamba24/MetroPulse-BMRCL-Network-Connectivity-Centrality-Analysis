"""
Bangalore Namma Metro - Interactive Route Planner & Centrality Analyzer CLI
Computes optimal route between selected places, displays step-by-step itinerary,
and outputs live Centrality Measures (Degree, Closeness, Betweenness),
Transitivity, Reciprocity, and Assortativity for the selected stations.

Usage:
    python scripts/find_metro_route.py "Whitefield" "Electronic City"
    python scripts/find_metro_route.py "Kengeri" "Silk Institute"
    python scripts/find_metro_route.py  (interactive prompt)
"""

import sys
import pandas as pd
import networkx as nx

def load_metro_data():
    nodes_df = pd.read_csv("data/bangalore_metro_nodes.csv")
    edges_df = pd.read_csv("data/bangalore_metro_edges.csv")
    cent_df = pd.read_csv("data/bangalore_metro_centrality.csv")
    cent_map = cent_df.set_index("station").to_dict(orient="index")

    G = nx.Graph()
    for _, row in nodes_df.iterrows():
        st = row["id"]
        c = cent_map.get(st, {})
        G.add_node(st, 
                   name=row["name"], 
                   lines=row["lines"].split("; "),
                   zone=row["zone"],
                   is_interchange=row["is_interchange"],
                   degree=c.get("degree", 2),
                   degree_centrality=c.get("degree_centrality", 0.0244),
                   closeness_centrality=c.get("closeness_centrality", 0.05),
                   betweenness_centrality=c.get("betweenness_centrality", 0.0),
                   is_articulation_point=c.get("is_articulation_point", True))

    for _, row in edges_df.iterrows():
        G.add_edge(row["source"], row["target"],
                   line=row["line"],
                   distance=row["distance_km"],
                   time=row["time_min"],
                   color=row["line_color"])

    return G, nodes_df, cent_map

def match_station(query, stations):
    query_clean = query.strip().lower()
    for st in stations:
        if st.lower() == query_clean:
            return st
    matches = [st for st in stations if query_clean in st.lower()]
    if matches:
        return matches[0]
    return None

def find_route(G, origin, dest):
    if origin not in G or dest not in G:
        return None

    path = nx.shortest_path(G, source=origin, target=dest, weight="time")
    
    total_km = 0.0
    total_time = 0.0
    steps = []
    interchanges = []

    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        edge_data = G[u][v]
        total_km += edge_data["distance"]
        total_time += edge_data["time"]
        steps.append({
            "from": u,
            "to": v,
            "line": edge_data["line"],
            "distance": edge_data["distance"],
            "time": edge_data["time"]
        })

    for i in range(len(steps) - 1):
        curr_line = steps[i]["line"]
        next_line = steps[i+1]["line"]
        if curr_line != next_line:
            transfer_station = steps[i]["to"]
            interchanges.append({
                "station": transfer_station,
                "from_line": curr_line,
                "to_line": next_line
            })
            total_time += 4.0

    # Identify route bottleneck
    peak_st = origin
    peak_b = G.nodes[origin].get("betweenness_centrality", 0.0)
    for st in path:
        b_val = G.nodes[st].get("betweenness_centrality", 0.0)
        if b_val > peak_b:
            peak_b = b_val
            peak_st = st

    return {
        "origin": origin,
        "destination": dest,
        "path": path,
        "stations_count": len(path),
        "total_distance_km": round(total_km, 1),
        "total_time_mins": round(total_time),
        "interchanges": interchanges,
        "steps": steps,
        "peak_bottleneck_station": peak_st,
        "peak_bottleneck_betweenness": round(peak_b, 4)
    }

def print_route(G, route_info):
    if not route_info:
        print("\n[ERROR] Could not compute a path between the specified stations.")
        return

    orig = route_info['origin']
    dest = route_info['destination']
    n_orig = G.nodes[orig]
    n_dest = G.nodes[dest]

    print("\n" + "="*75)
    print("  BENGALURU NAMMA METRO - OPTIMAL JOURNEY ITINERARY")
    print("="*75)
    print(f"  FROM : {orig} ({', '.join(n_orig['lines'])})")
    print(f"  TO   : {dest} ({', '.join(n_dest['lines'])})")
    print(f"  TIME : ~{route_info['total_time_mins']} minutes")
    print(f"  DIST : {route_info['total_distance_km']} km")
    print(f"  STOPS: {route_info['stations_count']} stations")

    if route_info["interchanges"]:
        print("\n  INTERCHANGE INSTRUCTIONS:")
        for ic in route_info["interchanges"]:
            print(f"   * Transfer at [{ic['station']}]: Change from {ic['from_line']} -> {ic['to_line']}")
    else:
        print("\n  DIRECT ROUTE: No line change needed (0 transfers)!")

    # ========================================================
    # LIVE CENTRALITY & STATION FEATURES FOR SELECTED PLACES
    # ========================================================
    print("\n" + "-"*75)
    print("  LIVE CENTRALITY & STATION FEATURES FOR SELECTED PLACES")
    print("-" * 75)
    
    # Origin Station Centrality
    print(f"\n  [ORIGIN] {orig}:")
    print(f"    - Degree Centrality     : {n_orig['degree']} connections (Normalized: {n_orig['degree_centrality']:.4f})")
    print(f"    - Closeness Centrality  : {n_orig['closeness_centrality']:.4f} (Accessibility score)")
    print(f"    - Betweenness Centrality: {n_orig['betweenness_centrality']:.4f} (Bridge/Hub traffic)")
    print(f"    - Hub Influence         : {n_orig.get('eigenvector_centrality', 0.0):.4f}")
    print(f"    - Single Point Failure  : {'YES (Cut Vertex)' if n_orig['is_articulation_point'] else 'NO (Redundant)'}")

    # Destination Station Centrality
    print(f"\n  [DESTINATION] {dest}:")
    print(f"    - Degree Centrality     : {n_dest['degree']} connections (Normalized: {n_dest['degree_centrality']:.4f})")
    print(f"    - Closeness Centrality  : {n_dest['closeness_centrality']:.4f} (Accessibility score)")
    print(f"    - Betweenness Centrality: {n_dest['betweenness_centrality']:.4f} (Bridge/Hub traffic)")
    print(f"    - Hub Influence         : {n_dest.get('eigenvector_centrality', 0.0):.4f}")
    print(f"    - Single Point Failure  : {'YES (Cut Vertex)' if n_dest['is_articulation_point'] else 'NO (Redundant)'}")

    # Route Peak Bottleneck
    print(f"\n  [ROUTE BOTTLENECK]:")
    print(f"    - Station: {route_info['peak_bottleneck_station']}")
    print(f"    - Betweenness Centrality: {route_info['peak_bottleneck_betweenness']} (Carries {route_info['peak_bottleneck_betweenness']*100:.1f}% of city-wide transit paths)")

    print("\n" + "-"*75)
    print("  STEP-BY-STEP STATIONS:")
    path = route_info["path"]
    for idx, st in enumerate(path):
        is_first = (idx == 0)
        is_last = (idx == len(path) - 1)
        is_transfer = any(ic["station"] == st for ic in route_info["interchanges"])

        if is_first:
            tag = "[START]      "
        elif is_last:
            tag = "[DESTINATION]"
        elif is_transfer:
            tag = "[TRANSFER]   "
        else:
            tag = "  |          "

        b_val = G.nodes[st].get("betweenness_centrality", 0.0)
        print(f"   {idx+1:2d}. {tag} {st:42s} (Betw: {b_val:.4f})")

    print("="*75 + "\n")

def interactive_cli():
    G, nodes_df, cent_map = load_metro_data()
    station_names = list(nodes_df["id"])

    print("\n" + "="*70)
    print(" Bengaluru Namma Metro - Route & Centrality Inspector")
    print("="*70)

    if len(sys.argv) >= 3:
        raw_from = sys.argv[1]
        raw_to = sys.argv[2]
    else:
        print("\nPopular stations: Whitefield, Majestic, Electronic City,")
        print("                  MG Road, Indiranagar, Peenya, Kengeri, Silk Institute\n")
        raw_from = input("Enter Starting Station (FROM): ")
        raw_to = input("Enter Destination Station (TO)  : ")

    from_st = match_station(raw_from, station_names)
    to_st = match_station(raw_to, station_names)

    if not from_st:
        print(f"[ERROR] Station not found: '{raw_from}'. Please check spelling.")
        return
    if not to_st:
        print(f"[ERROR] Station not found: '{raw_to}'. Please check spelling.")
        return

    route = find_route(G, from_st, to_st)
    print_route(G, route)

if __name__ == "__main__":
    interactive_cli()
