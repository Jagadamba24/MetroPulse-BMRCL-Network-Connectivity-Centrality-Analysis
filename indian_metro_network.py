"""
=============================================================================
INDIAN METRO CONNECTIVITY NETWORK: ANALYSIS & VISUALIZATION
Case Study: Bengaluru Namma Metro
=============================================================================
This script provides comprehensive network analysis using NetworkX & Matplotlib:
- Degree Centrality      : Finds stations with many direct connections
- Closeness Centrality   : Finds stations that can reach others efficiently
- Betweenness Centrality : Finds important bridge / interchange stations
- Transitivity           : Measures interconnected groups of stations (clustering)
- Reciprocity            : Measures two-way connections in a directed network
- Assortativity          : Measures whether similarly connected stations connect
- Station Comparison     : Compares metrics between origin and destination
- Network Visualization  : Displays the network with hub sizing & line colors
=============================================================================
"""

import os
import networkx as nx
import matplotlib.pyplot as plt

# ---------------------------------------------------
# 0. ANALYSIS PURPOSE REFERENCE TABLE
# ---------------------------------------------------
ANALYSIS_PURPOSE = [
    ("Degree Centrality", "Finds stations with many direct connections"),
    ("Closeness Centrality", "Finds stations that can reach others efficiently"),
    ("Betweenness Centrality", "Finds important bridge/interchange stations"),
    ("Transitivity", "Measures interconnected groups of stations"),
    ("Reciprocity", "Measures two-way connections in a directed network"),
    ("Assortativity", "Measures whether similarly connected stations tend to connect"),
    ("Network Visualization", "Displays the metro network graphically"),
]

def print_purpose_table():
    print("\n" + "=" * 80)
    print("           INDIAN METRO NETWORK ANALYSIS FRAMEWORK")
    print("=" * 80)
    print(f"{'Analysis':<26} | {'Purpose':<50}")
    print("-" * 26 + "-+-" + "-" * 50)
    for analysis, purpose in ANALYSIS_PURPOSE:
        print(f"{analysis:<26} | {purpose:<50}")
    print("=" * 80)


# ---------------------------------------------------
# 1. BUILD THE METRO NETWORK GRAPH
# ---------------------------------------------------
# Create an undirected metro network
G = nx.Graph()

# Option A: Check if the full project dataset exists
csv_edges_path = os.path.join(os.path.dirname(__file__), "data", "bangalore_metro_edges.csv")

if os.path.exists(csv_edges_path):
    import pandas as pd
    edges_df = pd.read_csv(csv_edges_path)
    for _, row in edges_df.iterrows():
        G.add_edge(row["source"], row["target"], line=row.get("line", "Metro Line"))
    network_source_label = f"Full Bengaluru Metro Network ({G.number_of_nodes()} stations, {G.number_of_edges()} track segments)"
else:
    # Option B: Complete Standalone multi-line corridor intersecting at Majestic
    purple_edges = [
        ("Challegatta", "Kengeri"),
        ("Kengeri", "Mysore Road"),
        ("Mysore Road", "Deepanjali Nagar"),
        ("Deepanjali Nagar", "Attiguppe"),
        ("Attiguppe", "Vijayanagar"),
        ("Vijayanagar", "Hosahalli"),
        ("Hosahalli", "Magadi Road"),
        ("Magadi Road", "City Railway Station"),
        ("City Railway Station", "Majestic"),
        ("Majestic", "Sir M Visveshwaraya"),
        ("Sir M Visveshwaraya", "Vidhana Soudha"),
        ("Vidhana Soudha", "Cubbon Park"),
        ("Cubbon Park", "MG Road"),
        ("MG Road", "Trinity"),
        ("Trinity", "Halasuru"),
        ("Halasuru", "Indiranagar"),
        ("Indiranagar", "Swami Vivekananda Road"),
        ("Swami Vivekananda Road", "Baiyappanahalli"),
        ("Baiyappanahalli", "KR Pura"),
        ("KR Pura", "Whitefield (Kadugodi)")
    ]

    green_edges = [
        ("Nagasandra", "Yeshwanthpur"),
        ("Yeshwanthpur", "Rajajinagar"),
        ("Rajajinagar", "Sampige Road"),
        ("Sampige Road", "Majestic"),              # Primary central interchange
        ("Majestic", "Chickpete"),
        ("Chickpete", "Krishna Rajendra Market"),
        ("Krishna Rajendra Market", "National College"),
        ("National College", "Lalbagh"),
        ("Lalbagh", "Jayanagar"),
        ("Jayanagar", "RV Road"),
        ("RV Road", "Banashankari"),
        ("Banashankari", "JP Nagar"),
        ("JP Nagar", "Yelachenahalli"),
        ("Yelachenahalli", "Silk Institute")
    ]

    yellow_edges = [
        ("RV Road", "Jayadeva Hospital"),          # Secondary interchange
        ("Jayadeva Hospital", "Central Silk Board"),
        ("Central Silk Board", "Electronic City")
    ]

    for u, v in purple_edges:
        G.add_edge(u, v, line="Purple Line")
    for u, v in green_edges:
        G.add_edge(u, v, line="Green Line")
    for u, v in yellow_edges:
        G.add_edge(u, v, line="Yellow Line")

    network_source_label = f"Bengaluru Metro Multi-Line Network ({G.number_of_nodes()} stations, {G.number_of_edges()} connections)"

# Print summary table and network info
print_purpose_table()
print(f"\n===== METRO NETWORK INFORMATION =====")
print(f"Dataset              : {network_source_label}")
print(f"Number of Stations   : {G.number_of_nodes()}")
print(f"Number of Connections: {G.number_of_edges()}")
print(f"Network Diameter     : {nx.diameter(G) if nx.is_connected(G) else 'Disconnected'} hops")
print(f"Average Path Length  : {nx.average_shortest_path_length(G):.2f} hops" if nx.is_connected(G) else "")


# ---------------------------------------------------
# 2. DEGREE CENTRALITY
# Purpose: Finds stations with many direct connections
# ---------------------------------------------------
degree = nx.degree_centrality(G)

print("\n" + "=" * 50)
print("1. DEGREE CENTRALITY")
print("   Purpose: Finds stations with many direct connections")
print("=" * 50)
top_degree = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:5]
for rank, (station, val) in enumerate(top_degree, 1):
    raw_deg = G.degree[station]
    print(f"  #{rank} {station:<35}: {val:.4f} ({raw_deg} direct track lines)")


# ---------------------------------------------------
# 3. CLOSENESS CENTRALITY
# Purpose: Finds stations that can reach others efficiently
# ---------------------------------------------------
closeness = nx.closeness_centrality(G)

print("\n" + "=" * 50)
print("2. CLOSENESS CENTRALITY")
print("   Purpose: Finds stations that can reach others efficiently")
print("=" * 50)
top_closeness = sorted(closeness.items(), key=lambda x: x[1], reverse=True)[:5]
for rank, (station, val) in enumerate(top_closeness, 1):
    print(f"  #{rank} {station:<35}: {val:.4f} (High central accessibility)")


# ---------------------------------------------------
# 4. BETWEENNESS CENTRALITY
# Purpose: Finds important bridge/interchange stations
# ---------------------------------------------------
betweenness = nx.betweenness_centrality(G)

print("\n" + "=" * 50)
print("3. BETWEENNESS CENTRALITY")
print("   Purpose: Finds important bridge/interchange stations")
print("=" * 50)
top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
for rank, (station, val) in enumerate(top_betweenness, 1):
    load_pct = val * 100
    print(f"  #{rank} {station:<35}: {val:.4f} (Carries {load_pct:.1f}% of shortest transit paths)")


# ---------------------------------------------------
# 5. EIGENVECTOR CENTRALITY & PAGERANK (Hub Prestige)
# ---------------------------------------------------
try:
    eigenvector = nx.eigenvector_centrality(G, max_iter=2000, tol=1e-04)
except Exception:
    eigenvector = closeness

try:
    pagerank = nx.pagerank(G)
except Exception:
    pagerank = degree


# ---------------------------------------------------
# 6. NETWORK TRANSITIVITY
# Purpose: Measures interconnected groups of stations
# ---------------------------------------------------
transitivity = nx.transitivity(G)

print("\n" + "=" * 50)
print("4. NETWORK TRANSITIVITY")
print("   Purpose: Measures interconnected groups of stations (clustering)")
print("=" * 50)
print(f"  Transitivity (Global Clustering): {transitivity:.4f}")
print("  Insight: Tree/line topologies have 0.0000 transitivity because metro tracks")
print("           run as arterial branches without redundant triangular loops.")


# ---------------------------------------------------
# 7. RECIPROCITY
# Purpose: Measures two-way connections in a directed network
# ---------------------------------------------------
# Metro connections are normally twin-track bidirectional (undirected).
# When modeled as a directed transit network (trains run in both directions A->B and B->A):
D = G.to_directed()
reciprocity = nx.reciprocity(D)

print("\n" + "=" * 50)
print("5. RECIPROCITY")
print("   Purpose: Measures two-way connections in a directed network")
print("=" * 50)
print(f"  Reciprocity: {reciprocity:.4f} (100% bidirectional dedicated twin-track service)")


# ---------------------------------------------------
# 8. ASSORTATIVITY
# Purpose: Measures whether similarly connected stations tend to connect
# ---------------------------------------------------
assortativity = nx.degree_assortativity_coefficient(G)

print("\n" + "=" * 50)
print("6. DEGREE ASSORTATIVITY")
print("   Purpose: Measures whether similarly connected stations tend to connect")
print("=" * 50)
print(f"  Degree Assortativity: {assortativity:.4f}")
if assortativity < 0:
    print("  Insight: Disassortative network. High-degree transfer hubs connect to")
    print("           many low-degree local corridor stations (radial hub-and-spoke).")
else:
    print("  Insight: Assortative network. Hubs connect predominantly to other hubs.")


# ---------------------------------------------------
# 9. MOST IMPORTANT STATIONS SUMMARY
# ---------------------------------------------------
print("\n" + "=" * 50)
print("7. MOST IMPORTANT STATIONS SUMMARY")
print("=" * 50)

highest_degree = max(degree, key=degree.get)
highest_closeness = max(closeness, key=closeness.get)
highest_betweenness = max(betweenness, key=betweenness.get)
highest_eigen = max(eigenvector, key=eigenvector.get)
highest_pr = max(pagerank, key=pagerank.get)

print(f"  Highest Degree (Most Tracks)    : {highest_degree} ({G.degree[highest_degree]} tracks)")
print(f"  Highest Closeness (Most Central): {highest_closeness} (Score: {closeness[highest_closeness]:.4f})")
print(f"  Highest Betweenness (Key Bridge): {highest_betweenness} (Load: {betweenness[highest_betweenness]*100:.1f}%)")
print(f"  Highest Hub Influence (Prestige): {highest_eigen} (Score: {eigenvector[highest_eigen]:.4f})")
print(f"  Highest Passenger Flow (PageRank): {highest_pr} (Score: {pagerank[highest_pr]:.4f})")


# ---------------------------------------------------
# 10. STATION COMPARISON FUNCTION (Origin vs Destination)
# ---------------------------------------------------
def compare_stations(station_a, station_b):
    if station_a not in G or station_b not in G:
        print(f"\n[!] Station '{station_a}' or '{station_b}' not found in network.")
        return

    print("\n" + "=" * 70)
    print(f"STATION COMPARISON: {station_a}  VS  {station_b}")
    print("=" * 70)
    print(f"{'Feature':<28} | {station_a[:18]:<18} | {station_b[:18]:<18} | {'Winner / Insight'}")
    print("-" * 28 + "-+-" + "-" * 18 + "-+-" + "-" * 18 + "-+-" + "-" * 16)
    
    # Degree
    d_a, d_b = G.degree[station_a], G.degree[station_b]
    w_deg = station_a if d_a > d_b else (station_b if d_b > d_a else "Equal")
    print(f"{'Direct Tracks (Degree)':<28} | {d_a:<18} | {d_b:<18} | {w_deg}")

    # Closeness
    c_a, c_b = closeness[station_a], closeness[station_b]
    w_close = station_a if c_a > c_b else (station_b if c_b > c_a else "Equal")
    print(f"{'Accessibility (Closeness)':<28} | {c_a:<18.4f} | {c_b:<18.4f} | {w_close}")

    # Betweenness
    b_a, b_b = betweenness[station_a], betweenness[station_b]
    w_bet = station_a if b_a > b_b else (station_b if b_b > b_a else "Equal")
    print(f"{'Traffic Load (Betweenness)':<28} | {f'{b_a*100:.1f}%':<18} | {f'{b_b*100:.1f}%':<18} | {w_bet}")

    # Eigenvector
    e_a, e_b = eigenvector[station_a], eigenvector[station_b]
    w_eig = station_a if e_a > e_b else (station_b if e_b > e_a else "Equal")
    print(f"{'Hub Influence (Eigenvector)':<28} | {e_a:<18.4f} | {e_b:<18.4f} | {w_eig}")

    # Shortest path between them
    if nx.has_path(G, station_a, station_b):
        path = nx.shortest_path(G, station_a, station_b)
        print("-" * 70)
        print(f"Optimal Shortest Route ({len(path)-1} hops, {len(path)} stations):")
        print(" -> ".join(path[:4]) + (" -> ... -> " + path[-1] if len(path) > 4 else ""))
    print("=" * 70)

# Quick demonstration comparison between Whitefield and Silk Institute
compare_origin = "Whitefield (Kadugodi)" if "Whitefield (Kadugodi)" in G else list(G.nodes())[0]
compare_dest = "Silk Institute" if "Silk Institute" in G else list(G.nodes())[-1]
compare_stations(compare_origin, compare_dest)


# ---------------------------------------------------
# 11. NETWORK VISUALIZATION
# Purpose: Displays the metro network graphically
# ---------------------------------------------------
print("\n===== 8. NETWORK VISUALIZATION =====")
print("Rendering network graph plot...")

plt.figure(figsize=(15, 10))
plt.style.use('dark_background')

# Layout
pos = nx.spring_layout(G, seed=42, k=0.35)

# Size nodes proportional to betweenness centrality (major hubs stand out)
node_sizes = [600 + (betweenness[n] * 4000) for n in G.nodes()]

# Color nodes: interchanges/hubs gold, others cyan
node_colors = []
for n in G.nodes():
    if G.degree[n] >= 3 or betweenness[n] > 0.2:
        node_colors.append("#fbbf24") # Major Hub / Interchange (Gold)
    else:
        node_colors.append("#38bdf8") # Corridor Station (Cyan)

# Draw edges
nx.draw_networkx_edges(G, pos, width=2.2, edge_color="#94a3b8", alpha=0.7)

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, edgecolors="#ffffff", linewidths=1.2)

# Draw labels with clean readable font
nx.draw_networkx_labels(G, pos, font_size=8, font_color="#ffffff", font_family="sans-serif", font_weight="bold")

plt.title(
    "Indian Metro Connectivity Network - Bengaluru Namma Metro\n"
    "Node Size ~ Betweenness Centrality (Traffic Load) | Gold Nodes ~ Major Interchange Hubs",
    fontsize=13,
    fontweight="bold",
    pad=15,
    color="#f8fafc"
)
plt.axis("off")
plt.tight_layout()

# Save visualization image
output_img = "metro_network_analysis.png"
plt.savefig(output_img, dpi=300, bbox_inches="tight", facecolor="#0f172a")
print(f"Visualization saved to: {output_img}")

# Show plot if running in interactive display
try:
    plt.show(block=False)
except Exception:
    pass

print("\nAnalysis completed successfully!")
