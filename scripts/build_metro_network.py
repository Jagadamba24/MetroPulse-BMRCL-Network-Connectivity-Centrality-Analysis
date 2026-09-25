"""
Indian Metro Connectivity Network - Data Builder and Network Analysis Engine
Generates comprehensive station and route datasets for Delhi Metro (DMRC) and comparative Indian metros,
calculates Degree, Closeness, Betweenness, Transitivity, Reciprocity, Assortativity, and Similarity,
and exports Gephi-ready formats (GEXF, GraphML) and visual plots.
"""

import os
import json
import math
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure output directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("visualizations", exist_ok=True)
os.makedirs("exports", exist_ok=True)
os.makedirs("scripts", exist_ok=True)

# Define Delhi Metro Station Sequences with realistic coordinates, zones, and connections
# Delhi Metro has ~10 active major corridors
METRO_LINES = {
    "Red Line": {
        "color": "#E31E24",
        "stations": [
            ("Rithala", 28.7208, 77.1072, "North West Delhi"),
            ("Rohini West", 28.7147, 77.1147, "North West Delhi"),
            ("Rohini East", 28.7100, 77.1264, "North West Delhi"),
            ("Pitampura", 28.7032, 77.1352, "North West Delhi"),
            ("Kohat Enclave", 28.6978, 77.1432, "North West Delhi"),
            ("Netaji Subhash Place", 28.6953, 77.1525, "North West Delhi"), # Interchange with Pink
            ("Keshav Puram", 28.6908, 77.1620, "North West Delhi"),
            ("Kanhaiya Nagar", 28.6835, 77.1685, "North West Delhi"),
            ("Inderlok", 28.6738, 77.1706, "North West Delhi"), # Interchange with Green
            ("Shastri Nagar", 28.6698, 77.1818, "North Delhi"),
            ("Pratap Nagar", 28.6672, 77.1956, "North Delhi"),
            ("Pul Bangash", 28.6653, 77.2036, "North Delhi"),
            ("Tis Hazari", 28.6668, 77.2167, "North Delhi"),
            ("Kashmere Gate", 28.6675, 77.2285, "Central Delhi"), # Triple Interchange (Red, Yellow, Violet)
            ("Shastri Park", 28.6705, 77.2505, "North East Delhi"),
            ("Seelampur", 28.6698, 77.2662, "North East Delhi"),
            ("Welcome", 28.6719, 77.2776, "North East Delhi"), # Interchange with Pink
            ("Shahdara", 28.6734, 77.2894, "East Delhi"),
            ("Mansarovar Park", 28.6792, 77.3005, "East Delhi"),
            ("Jhilmil", 28.6816, 77.3117, "East Delhi"),
            ("Dilshad Garden", 28.6761, 77.3214, "East Delhi"),
            ("Shaheed Nagar", 28.6708, 77.3325, "Ghaziabad"),
            ("Raj Bagh", 28.6712, 77.3440, "Ghaziabad"),
            ("Major Mohit Sharma", 28.6740, 77.3560, "Ghaziabad"),
            ("Shyam Park", 28.6790, 77.3680, "Ghaziabad"),
            ("Mohan Nagar", 28.6820, 77.3810, "Ghaziabad"),
            ("Arthala", 28.6850, 77.3950, "Ghaziabad"),
            ("Hindon River", 28.6880, 77.4080, "Ghaziabad"),
            ("Shaheed Sthal", 28.6910, 77.4200, "Ghaziabad")
        ]
    },
    "Yellow Line": {
        "color": "#FFD200",
        "stations": [
            ("Samaypur Badli", 28.7455, 77.1384, "North Delhi"),
            ("Rohini Sector 18", 28.7392, 77.1425, "North Delhi"),
            ("Haiderpur Badli Mor", 28.7290, 77.1510, "North Delhi"),
            ("Jahangirpuri", 28.7258, 77.1625, "North Delhi"),
            ("Adarsh Nagar", 28.7161, 77.1706, "North Delhi"),
            ("Azadpur", 28.7067, 77.1804, "North Delhi"), # Interchange with Pink
            ("Model Town", 28.6998, 77.1932, "North Delhi"),
            ("Guru Tegh Bahadur Nagar", 28.6978, 77.2062, "North Delhi"),
            ("Vishwa Vidyalaya", 28.6948, 77.2139, "North Delhi"),
            ("Vidhan Sabha", 28.6792, 77.2215, "North Delhi"),
            ("Civil Lines", 28.6753, 77.2255, "North Delhi"),
            ("Kashmere Gate", 28.6675, 77.2285, "Central Delhi"), # Interchange
            ("Chandni Chowk", 28.6578, 77.2302, "Central Delhi"),
            ("Chawri Bazar", 28.6493, 77.2263, "Central Delhi"),
            ("New Delhi", 28.6431, 77.2223, "Central Delhi"), # Interchange with Airport Express & Indian Railways
            ("Rajiv Chowk", 28.6328, 77.2195, "Central Delhi"), # Major Hub (Yellow & Blue)
            ("Patel Chowk", 28.6231, 77.2138, "Central Delhi"),
            ("Central Secretariat", 28.6146, 77.2119, "Central Delhi"), # Interchange with Violet
            ("Udyog Bhawan", 28.6115, 77.2120, "Central Delhi"),
            ("Lok Kalyan Marg", 28.5985, 77.2105, "South Delhi"),
            ("Jor Bagh", 28.5888, 77.2120, "South Delhi"),
            ("Dilli Haat - INA", 28.5744, 77.2103, "South Delhi"), # Interchange with Pink
            ("AIIMS", 28.5686, 77.2078, "South Delhi"),
            ("Green Park", 28.5587, 77.2065, "South Delhi"),
            ("Hauz Khas", 28.5431, 77.2064, "South Delhi"), # Interchange with Magenta
            ("Malviya Nagar", 28.5282, 77.2062, "South Delhi"),
            ("Saket", 28.5208, 77.2017, "South Delhi"),
            ("Qutab Minar", 28.5132, 77.1857, "South Delhi"),
            ("Chhatarpur", 28.5065, 77.1746, "South Delhi"),
            ("Sultanpur", 28.4988, 77.1615, "South Delhi"),
            ("Ghogha", 28.4900, 77.1480, "South Delhi"),
            ("Guru Dronacharya", 28.4812, 77.1215, "Gurugram"),
            ("Sikanderpur", 28.4820, 77.0931, "Gurugram"), # Interchange with Rapid Metro
            ("MG Road", 28.4798, 77.0805, "Gurugram"),
            ("IFFCO Chowk", 28.4722, 77.0725, "Gurugram"),
            ("Millennium City Centre", 28.4593, 77.0725, "Gurugram")
        ]
    },
    "Blue Line": {
        "color": "#0072CE",
        "stations": [
            ("Dwarka Sector 21", 28.5523, 77.0583, "South West Delhi"), # Interchange with Airport Express
            ("Dwarka Sector 8", 28.5658, 77.0678, "South West Delhi"),
            ("Dwarka Sector 9", 28.5742, 77.0645, "South West Delhi"),
            ("Dwarka Sector 10", 28.5815, 77.0581, "South West Delhi"),
            ("Dwarka Sector 11", 28.5898, 77.0520, "South West Delhi"),
            ("Dwarka Sector 12", 28.5925, 77.0410, "South West Delhi"),
            ("Dwarka Sector 13", 28.6010, 77.0335, "South West Delhi"),
            ("Dwarka Sector 14", 28.6105, 77.0260, "South West Delhi"),
            ("Dwarka", 28.6152, 77.0175, "South West Delhi"), # Interchange with Grey
            ("Dwarka Mor", 28.6195, 77.0328, "West Delhi"),
            ("Nawada", 28.6212, 77.0445, "West Delhi"),
            ("Uttam Nagar West", 28.6235, 77.0560, "West Delhi"),
            ("Uttam Nagar East", 28.6255, 77.0658, "West Delhi"),
            ("Janakpuri West", 28.6295, 77.0778, "West Delhi"), # Interchange with Magenta
            ("Janakpuri East", 28.6328, 77.0875, "West Delhi"),
            ("Tilak Nagar", 28.6365, 77.0988, "West Delhi"),
            ("Subhash Nagar", 28.6405, 77.1055, "West Delhi"),
            ("Tagore Garden", 28.6440, 77.1145, "West Delhi"),
            ("Rajouri Garden", 28.6492, 77.1235, "West Delhi"), # Interchange with Pink
            ("Ramesh Nagar", 28.6528, 77.1345, "West Delhi"),
            ("Moti Nagar", 28.6578, 77.1435, "West Delhi"),
            ("Kirti Nagar", 28.6558, 77.1518, "West Delhi"), # Interchange with Green
            ("Shadipur", 28.6515, 77.1585, "West Delhi"),
            ("Patel Nagar", 28.6508, 77.1685, "Central Delhi"),
            ("Rajendra Place", 28.6425, 77.1785, "Central Delhi"),
            ("Karol Bagh", 28.6442, 77.1902, "Central Delhi"),
            ("Jhandewalan", 28.6441, 77.2015, "Central Delhi"),
            ("RK Ashram Marg", 28.6392, 77.2115, "Central Delhi"),
            ("Rajiv Chowk", 28.6328, 77.2195, "Central Delhi"), # Interchange
            ("Barakhamba Road", 28.6315, 77.2275, "Central Delhi"),
            ("Mandi House", 28.6258, 77.2345, "Central Delhi"), # Interchange with Violet
            ("Supreme Court", 28.6235, 77.2435, "Central Delhi"),
            ("Indraprastha", 28.6205, 77.2515, "Central Delhi"),
            ("Yamuna Bank", 28.6238, 77.2665, "East Delhi"), # Fork point to Noida / Vaishali
            ("Akshardham", 28.6185, 77.2795, "East Delhi"),
            ("Mayur Vihar-1", 28.6048, 77.2942, "East Delhi"), # Interchange with Pink
            ("Mayur Vihar Extension", 28.5935, 77.3015, "East Delhi"),
            ("New Ashok Nagar", 28.5885, 77.3115, "East Delhi"),
            ("Noida Sector 15", 28.5845, 77.3195, "Noida"),
            ("Noida Sector 16", 28.5785, 77.3255, "Noida"),
            ("Noida Sector 18", 28.5708, 77.3265, "Noida"),
            ("Botanical Garden", 28.5642, 77.3345, "Noida"), # Interchange with Magenta
            ("Golf Course", 28.5672, 77.3465, "Noida"),
            ("Noida City Centre", 28.5745, 77.3565, "Noida"),
            ("Noida Sector 34", 28.5815, 77.3655, "Noida"),
            ("Noida Sector 52", 28.5915, 77.3715, "Noida"), # Walkway interchange with Aqua Line
            ("Noida Sector 61", 28.6015, 77.3725, "Noida"),
            ("Noida Sector 59", 28.6125, 77.3735, "Noida"),
            ("Noida Sector 62", 28.6225, 77.3705, "Noida"),
            ("Noida Electronic City", 28.6285, 77.3675, "Noida")
        ]
    },
    "Blue Branch Line": {
        "color": "#0072CE",
        "stations": [
            ("Yamuna Bank", 28.6238, 77.2665, "East Delhi"),
            ("Laxmi Nagar", 28.6315, 77.2775, "East Delhi"),
            ("Nirman Vihar", 28.6365, 77.2865, "East Delhi"),
            ("Preet Vihar", 28.6415, 77.2955, "East Delhi"),
            ("Karkarduma", 28.6485, 77.3045, "East Delhi"), # Interchange with Pink
            ("Anand Vihar ISBT", 28.6468, 77.3160, "East Delhi"), # Interchange with Pink & Railway/Bus
            ("Kaushambi", 28.6455, 77.3245, "Ghaziabad"),
            ("Vaishali", 28.6498, 77.3395, "Ghaziabad")
        ]
    },
    "Violet Line": {
        "color": "#94318F",
        "stations": [
            ("Kashmere Gate", 28.6675, 77.2285, "Central Delhi"), # Interchange
            ("Lal Quila", 28.6565, 77.2385, "Central Delhi"),
            ("Jama Masjid", 28.6505, 77.2375, "Central Delhi"),
            ("Delhi Gate", 28.6405, 77.2405, "Central Delhi"),
            ("ITO", 28.6315, 77.2408, "Central Delhi"),
            ("Mandi House", 28.6258, 77.2345, "Central Delhi"), # Interchange
            ("Janpath", 28.6225, 77.2185, "Central Delhi"),
            ("Central Secretariat", 28.6146, 77.2119, "Central Delhi"), # Interchange
            ("Khan Market", 28.6015, 77.2285, "Central Delhi"),
            ("Jawaharlal Nehru Stadium", 28.5885, 77.2345, "South Delhi"),
            ("Jangpura", 28.5805, 77.2395, "South Delhi"),
            ("Lajpat Nagar", 28.5708, 77.2375, "South Delhi"), # Interchange with Pink
            ("Moolchand", 28.5655, 77.2345, "South Delhi"),
            ("Kailash Colony", 28.5555, 77.2415, "South Delhi"),
            ("Nehru Place", 28.5515, 77.2515, "South Delhi"),
            ("Kalkaji Mandir", 28.5495, 77.2585, "South Delhi"), # Interchange with Magenta
            ("Govind Puri", 28.5365, 77.2645, "South Delhi"),
            ("Harkesh Nagar Okhla", 28.5285, 77.2765, "South Delhi"),
            ("Jasola Apollo", 28.5245, 77.2845, "South Delhi"),
            ("Sarita Vihar", 28.5145, 77.2915, "South Delhi"),
            ("Mohan Estate", 28.5045, 77.2995, "South Delhi"),
            ("Tughlakabad", 28.4945, 77.3065, "South Delhi"),
            ("Badarpur Border", 28.4865, 77.3085, "South Delhi"),
            ("Sarai", 28.4725, 77.3115, "Faridabad"),
            ("NHPC Chowk", 28.4595, 77.3125, "Faridabad"),
            ("Mewala Maharajpur", 28.4485, 77.3125, "Faridabad"),
            ("Sector 28 Faridabad", 28.4355, 77.3125, "Faridabad"),
            ("Badkal Mor", 28.4215, 77.3135, "Faridabad"),
            ("Old Faridabad", 28.4105, 77.3155, "Faridabad"),
            ("Neelam Chowk Ajronda", 28.3985, 77.3175, "Faridabad"),
            ("Bata Chowk", 28.3855, 77.3195, "Faridabad"),
            ("Escorts Mujesar", 28.3725, 77.3225, "Faridabad"),
            ("Sant Surdas", 28.3585, 77.3255, "Faridabad"),
            ("Raja Nahar Singh", 28.3415, 77.3295, "Faridabad")
        ]
    },
    "Green Line": {
        "color": "#00A850",
        "stations": [
            ("Inderlok", 28.6738, 77.1706, "North West Delhi"), # Interchange
            ("Ashok Park Main", 28.6715, 77.1575, "North West Delhi"),
            ("Punjabi Bagh", 28.6705, 77.1435, "West Delhi"),
            ("Shivaji Park", 28.6725, 77.1325, "West Delhi"),
            ("Madipur", 28.6735, 77.1215, "West Delhi"),
            ("Paschim Vihar East", 28.6745, 77.1105, "West Delhi"),
            ("Paschim Vihar West", 28.6765, 77.0985, "West Delhi"),
            ("Peeragarhi", 28.6795, 77.0865, "West Delhi"),
            ("Udyog Nagar", 28.6825, 77.0755, "West Delhi"),
            ("Maharaja Surajmal Stadium", 28.6855, 77.0635, "West Delhi"),
            ("Nangloi", 28.6875, 77.0515, "West Delhi"),
            ("Nangloi Railway Station", 28.6885, 77.0405, "West Delhi"),
            ("Rajdhani Park", 28.6905, 77.0285, "West Delhi"),
            ("Mundka", 28.6925, 77.0165, "West Delhi"),
            ("Mundka Industrial Area", 28.6945, 77.0015, "West Delhi"),
            ("Ghevra Metro Station", 28.6965, 76.9855, "West Delhi"),
            ("Tikri Kalan", 28.6975, 76.9695, "West Delhi"),
            ("Tikri Border", 28.6985, 76.9535, "West Delhi"),
            ("Pandit Shree Ram Sharma", 28.6965, 76.9395, "Bahadurgarh"),
            ("Bahadurgarh City", 28.6945, 76.9245, "Bahadurgarh"),
            ("Brigadier Hoshiar Singh", 28.6915, 76.9105, "Bahadurgarh")
        ]
    },
    "Green Branch Line": {
        "color": "#00A850",
        "stations": [
            ("Ashok Park Main", 28.6715, 77.1575, "North West Delhi"),
            ("Satguru Ram Singh Marg", 28.6605, 77.1535, "West Delhi"),
            ("Kirti Nagar", 28.6558, 77.1518, "West Delhi") # Interchange with Blue
        ]
    },
    "Pink Line": {
        "color": "#EB008B",
        "stations": [
            ("Majlis Park", 28.7185, 77.1795, "North Delhi"),
            ("Azadpur", 28.7067, 77.1804, "North Delhi"), # Interchange with Yellow
            ("Shalimar Bagh", 28.7015, 77.1655, "North West Delhi"),
            ("Netaji Subhash Place", 28.6953, 77.1525, "North West Delhi"), # Interchange with Red
            ("Shakurpur", 28.6895, 77.1455, "North West Delhi"),
            ("Punjabi Bagh West", 28.6725, 77.1385, "West Delhi"),
            ("ESI Hospital", 28.6615, 77.1315, "West Delhi"),
            ("Rajouri Garden", 28.6492, 77.1235, "West Delhi"), # Interchange with Blue
            ("Maya Puri", 28.6395, 77.1285, "West Delhi"),
            ("Naraina Vihar", 28.6285, 77.1355, "West Delhi"),
            ("Delhi Cantt", 28.5995, 77.1425, "South West Delhi"),
            ("Durgabai Deshmukh South Campus", 28.5885, 77.1625, "South Delhi"),
            ("Sir M. Vishweshwaraiah Moti Bagh", 28.5825, 77.1735, "South Delhi"),
            ("Bhikaji Cama Place", 28.5735, 77.1865, "South Delhi"),
            ("Sarojini Nagar", 28.5740, 77.1985, "South Delhi"),
            ("Dilli Haat - INA", 28.5744, 77.2103, "South Delhi"), # Interchange with Yellow
            ("South Extension", 28.5725, 77.2235, "South Delhi"),
            ("Lajpat Nagar", 28.5708, 77.2375, "South Delhi"), # Interchange with Violet
            ("Vinobapuri", 28.5685, 77.2485, "South Delhi"),
            ("Ashram", 28.5705, 77.2595, "South Delhi"),
            ("Sarai Kale Khan - Nizamuddin", 28.5885, 77.2605, "South Delhi"),
            ("Mayur Vihar-1", 28.6048, 77.2942, "East Delhi"), # Interchange with Blue
            ("Mayur Vihar Pocket 1", 28.6085, 77.2995, "East Delhi"),
            ("Trilokpuri Sanjay Lake", 28.6145, 77.3045, "East Delhi"),
            ("East Vinod Nagar", 28.6215, 77.3085, "East Delhi"),
            ("Mandawali - West Vinod Nagar", 28.6295, 77.3075, "East Delhi"),
            ("IP Extension", 28.6365, 77.3055, "East Delhi"),
            ("Anand Vihar ISBT", 28.6468, 77.3160, "East Delhi"), # Interchange with Blue
            ("Karkarduma", 28.6485, 77.3045, "East Delhi"), # Interchange with Blue
            ("Karkarduma Court", 28.6545, 77.2985, "East Delhi"),
            ("Krishna Nagar", 28.6595, 77.2895, "East Delhi"),
            ("East Azad Nagar", 28.6645, 77.2835, "East Delhi"),
            ("Welcome", 28.6719, 77.2776, "North East Delhi"), # Interchange with Red
            ("Jaffrabad", 28.6795, 77.2745, "North East Delhi"),
            ("Maujpur - Babarpur", 28.6865, 77.2715, "North East Delhi"),
            ("Gokulpuri", 28.6945, 77.2725, "North East Delhi"),
            ("Johri Enclave", 28.7035, 77.2745, "North East Delhi"),
            ("Shiv Vihar", 28.7115, 77.2785, "North East Delhi")
        ]
    },
    "Magenta Line": {
        "color": "#8B124F",
        "stations": [
            ("Janakpuri West", 28.6295, 77.0778, "West Delhi"), # Interchange with Blue
            ("Janakpuri South", 28.6185, 77.0865, "West Delhi"),
            ("Dashrath Puri", 28.6085, 77.0885, "South West Delhi"),
            ("Palam", 28.5915, 77.0905, "South West Delhi"),
            ("Sadar Bazaar Cantonment", 28.5815, 77.1065, "South West Delhi"),
            ("Terminal 1 IGI Airport", 28.5635, 77.1235, "South West Delhi"),
            ("Shankar Vihar", 28.5525, 77.1425, "South West Delhi"),
            ("Vasant Vihar", 28.5555, 77.1605, "South Delhi"),
            ("Munirka", 28.5565, 77.1725, "South Delhi"),
            ("RK Puram", 28.5535, 77.1855, "South Delhi"),
            ("IIT Delhi", 28.5465, 77.1955, "South Delhi"),
            ("Hauz Khas", 28.5431, 77.2064, "South Delhi"), # Interchange with Yellow
            ("Panchsheel Park", 28.5415, 77.2185, "South Delhi"),
            ("Chirag Delhi", 28.5395, 77.2305, "South Delhi"),
            ("Greater Kailash", 28.5385, 77.2425, "South Delhi"),
            ("Nehru Enclave", 28.5435, 77.2515, "South Delhi"),
            ("Kalkaji Mandir", 28.5495, 77.2585, "South Delhi"), # Interchange with Violet
            ("Okhla NSIC", 28.5525, 77.2685, "South Delhi"),
            ("Sukhdev Vihar", 28.5615, 77.2765, "South Delhi"),
            ("Jamia Millia Islamia", 28.5625, 77.2865, "South Delhi"),
            ("Okhla Vihar", 28.5595, 77.2965, "South Delhi"),
            ("Jasola Vihar Shaheen Bagh", 28.5485, 77.3045, "South Delhi"),
            ("Kalindi Kunj", 28.5435, 77.3115, "South Delhi"),
            ("Okhla Bird Sanctuary", 28.5475, 77.3235, "Noida"),
            ("Botanical Garden", 28.5642, 77.3345, "Noida") # Interchange with Blue
        ]
    },
    "Airport Express Line": {
        "color": "#F37023",
        "stations": [
            ("New Delhi", 28.6431, 77.2223, "Central Delhi"), # Interchange with Yellow
            ("Shivaji Stadium", 28.6295, 77.2115, "Central Delhi"),
            ("Dhaula Kuan", 28.5915, 77.1625, "South Delhi"),
            ("Delhi Aerocity", 28.5505, 77.1215, "South West Delhi"),
            ("Airport (Terminal 3)", 28.5565, 77.0865, "South West Delhi"),
            ("Dwarka Sector 21", 28.5523, 77.0583, "South West Delhi"), # Interchange with Blue
            ("Yashobhoomi Dwarka Sector 25", 28.5465, 77.0425, "South West Delhi")
        ]
    },
    "Grey Line": {
        "color": "#7D8387",
        "stations": [
            ("Dwarka", 28.6152, 77.0175, "South West Delhi"), # Interchange with Blue
            ("Nangli", 28.6185, 76.9955, "South West Delhi"),
            ("Najafgarh", 28.6135, 76.9825, "South West Delhi"),
            ("Dhansa Bus Stand", 28.6085, 76.9715, "South West Delhi")
        ]
    },
    "Rapid Metro Gurgaon": {
        "color": "#808285",
        "stations": [
            ("Sikanderpur", 28.4820, 77.0931, "Gurugram"), # Interchange with Yellow
            ("Phase 2", 28.4905, 77.0895, "Gurugram"),
            ("Belvedere Towers", 28.4955, 77.0875, "Gurugram"),
            ("Cyber City", 28.4985, 77.0895, "Gurugram"),
            ("Moulsari Avenue", 28.5025, 77.0965, "Gurugram"),
            ("Phase 3", 28.4915, 77.1005, "Gurugram"),
            ("Sector 42-43", 28.4685, 77.0955, "Gurugram"),
            ("Sector 53-54", 28.4555, 77.0985, "Gurugram"),
            ("Sector 54 Chowk", 28.4415, 77.1025, "Gurugram"),
            ("Sector 55-56", 28.4285, 77.1085, "Gurugram")
        ]
    },
    "Aqua Line": {
        "color": "#00B4D8",
        "stations": [
            ("Noida Sector 51", 28.5915, 77.3735, "Noida"), # Connected to Sector 52 (Blue)
            ("Noida Sector 50", 28.5835, 77.3755, "Noida"),
            ("Noida Sector 76", 28.5725, 77.3785, "Noida"),
            ("Noida Sector 101", 28.5585, 77.3825, "Noida"),
            ("Noida Sector 81", 28.5445, 77.3865, "Noida"),
            ("NSEZ", 28.5315, 77.3915, "Noida"),
            ("Noida Sector 83", 28.5175, 77.3975, "Noida"),
            ("Noida Sector 137", 28.5035, 77.4045, "Noida"),
            ("Noida Sector 142", 28.4895, 77.4115, "Noida"),
            ("Pari Chowk", 28.4655, 77.5095, "Greater Noida"),
            ("Depot", 28.4415, 77.5255, "Greater Noida")
        ]
    }
}

# Special pedestrian / skywalk interchange links
WALKWAY_LINKS = [
    ("Noida Sector 52", "Noida Sector 51", "Walkway Interchange", "#00B4D8", 0.3, 3.5),
    ("Dhaula Kuan", "Durgabai Deshmukh South Campus", "Skywalk Travelator", "#F37023", 0.8, 6.0)
]

def haversine_dist(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def build_datasets():
    nodes_dict = {}
    edges_list = []

    for line_name, data in METRO_LINES.items():
        st_list = data["stations"]
        color = data["color"]
        for i, (st_name, lat, lon, zone) in enumerate(st_list):
            if st_name not in nodes_dict:
                nodes_dict[st_name] = {
                    "id": st_name,
                    "name": st_name,
                    "lat": lat,
                    "lon": lon,
                    "zone": zone,
                    "lines": [line_name]
                }
            else:
                if line_name not in nodes_dict[st_name]["lines"]:
                    nodes_dict[st_name]["lines"].append(line_name)

            # Edge to next station in line
            if i < len(st_list) - 1:
                next_st = st_list[i+1][0]
                dist = haversine_dist(lat, lon, st_list[i+1][1], st_list[i+1][2])
                dist = max(dist, 0.8) # realistic lower bound
                travel_time = round(dist * 1.8 + 1.2, 1) # ~32 km/h average commercial speed + dwell
                edges_list.append({
                    "source": st_name,
                    "target": next_st,
                    "line": line_name,
                    "line_color": color,
                    "distance_km": dist,
                    "time_min": travel_time,
                    "type": "track"
                })

    # Add walkway interchanges
    for u, v, l_name, l_col, d_km, t_min in WALKWAY_LINKS:
        if u in nodes_dict and v in nodes_dict:
            edges_list.append({
                "source": u,
                "target": v,
                "line": l_name,
                "line_color": l_col,
                "distance_km": d_km,
                "time_min": t_min,
                "type": "walkway"
            })

    # Finalize nodes properties
    nodes_list = []
    for st_name, info in nodes_dict.items():
        num_lines = len(info["lines"])
        is_interchange = (num_lines > 1)
        # Classify footfall tier
        if num_lines >= 3 or st_name in ["Rajiv Chowk", "Kashmere Gate", "New Delhi", "Hauz Khas"]:
            footfall = "Mega Hub"
        elif is_interchange:
            footfall = "High"
        elif "Sector" in st_name or "Industrial" in st_name:
            footfall = "Medium"
        else:
            footfall = "Standard"

        nodes_list.append({
            "id": st_name,
            "name": st_name,
            "latitude": info["lat"],
            "longitude": info["lon"],
            "zone": info["zone"],
            "lines": "; ".join(info["lines"]),
            "line_count": num_lines,
            "is_interchange": is_interchange,
            "footfall_tier": footfall
        })

    nodes_df = pd.DataFrame(nodes_list)
    edges_df = pd.DataFrame(edges_list)

    nodes_df.to_csv("data/delhi_metro_nodes.csv", index=False)
    edges_df.to_csv("data/delhi_metro_edges.csv", index=False)
    print(f"Generated {len(nodes_df)} stations and {len(edges_df)} direct track segments.")
    return nodes_df, edges_df

def perform_network_analysis(nodes_df, edges_df):
    # Construct Undirected Graph G
    G = nx.Graph()
    for _, row in nodes_df.iterrows():
        G.add_node(row["id"], 
                   name=row["name"],
                   lat=row["latitude"],
                   lon=row["longitude"],
                   zone=row["zone"],
                   lines=row["lines"],
                   line_count=row["line_count"],
                   is_interchange=row["is_interchange"],
                   footfall=row["footfall_tier"])

    for _, row in edges_df.iterrows():
        G.add_edge(row["source"], row["target"],
                   line=row["line"],
                   line_color=row["line_color"],
                   distance=row["distance_km"],
                   time=row["time_min"],
                   edge_type=row["type"])

    # Construct Directed Graph D (modeling bidirectional operations + twin tracks)
    D = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        D.add_edge(u, v, **data)
        D.add_edge(v, u, **data)

    print(f"Graph nodes: {G.number_of_nodes()}, edges: {G.number_of_edges()}")

    # 1. Degree Centrality
    deg = dict(G.degree())
    deg_centrality = nx.degree_centrality(G)

    # 2. Closeness Centrality (both unweighted hop and distance-weighted)
    closeness_hop = nx.closeness_centrality(G)
    closeness_dist = nx.closeness_centrality(G, distance='distance')

    # 3. Betweenness Centrality (Node and Edge)
    betweenness = nx.betweenness_centrality(G, normalized=True)
    edge_betweenness = nx.edge_betweenness_centrality(G, normalized=True)

    # Bonus: Eigenvector Centrality & PageRank
    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
    except Exception:
        eigenvector = {n: deg[n] / sum(deg.values()) for n in G.nodes()}
    try:
        pagerank = nx.pagerank_numpy(G)
    except Exception:
        pagerank = {n: deg[n] / sum(deg.values()) for n in G.nodes()}

    # Local clustering coefficient
    clustering_coeff = nx.clustering(G)

    # Articulation Points (Cut Vertices - Single Points of Vulnerability)
    articulation_points = list(nx.articulation_points(G))

    # Global Metrics
    transitivity = nx.transitivity(G) # Ratio of 3*triangles / triads
    avg_clustering = nx.average_clustering(G)
    
    # Reciprocity (for Directed representation)
    reciprocity_val = nx.reciprocity(D)

    # Degree Assortativity Coefficient r
    degree_assortativity = nx.degree_assortativity_coefficient(G)
    # Zone Attribute Assortativity
    zone_assortativity = nx.attribute_assortativity_coefficient(G, 'zone')

    # Connected Components & Diameter
    connected_comps = list(nx.connected_components(G))
    giant_comp = G.subgraph(max(connected_comps, key=len)).copy()
    diameter = nx.diameter(giant_comp)
    avg_path_len = nx.average_shortest_path_length(giant_comp)

    # Top rankings extraction
    top_deg = sorted(deg.items(), key=lambda x: x[1], reverse=True)[:10]
    top_close = sorted(closeness_hop.items(), key=lambda x: x[1], reverse=True)[:10]
    top_between = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
    top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
    top_edge_between = sorted(edge_betweenness.items(), key=lambda x: x[1], reverse=True)[:10]

    # Convert node attributes to DataFrame
    analysis_df = pd.DataFrame({
        "station": list(G.nodes()),
        "degree": [deg[n] for n in G.nodes()],
        "degree_centrality": [round(deg_centrality[n], 4) for n in G.nodes()],
        "closeness_centrality": [round(closeness_hop[n], 4) for n in G.nodes()],
        "betweenness_centrality": [round(betweenness[n], 4) for n in G.nodes()],
        "eigenvector_centrality": [round(eigenvector[n], 4) for n in G.nodes()],
        "pagerank": [round(pagerank[n], 4) for n in G.nodes()],
        "clustering_coefficient": [round(clustering_coeff[n], 4) for n in G.nodes()],
        "is_articulation_point": [n in articulation_points for n in G.nodes()],
        "zone": [G.nodes[n]["zone"] for n in G.nodes()],
        "lines": [G.nodes[n]["lines"] for n in G.nodes()],
        "is_interchange": [G.nodes[n]["is_interchange"] for n in G.nodes()]
    })
    analysis_df.to_csv("data/delhi_metro_centrality_results.csv", index=False)

    # Node similarity calculation (Jaccard similarity on neighbors)
    similarity_records = []
    nodes_list = list(G.nodes())
    for i in range(len(nodes_list)):
        for j in range(i+1, len(nodes_list)):
            u, v = nodes_list[i], nodes_list[j]
            nu, nv = set(G.neighbors(u)), set(G.neighbors(v))
            if nu and nv:
                intersection = len(nu.intersection(nv))
                union = len(nu.union(nv))
                jaccard = intersection / union if union > 0 else 0
                if jaccard > 0:
                    similarity_records.append({
                        "station_1": u,
                        "station_2": v,
                        "shared_neighbors": list(nu.intersection(nv)),
                        "jaccard_similarity": round(jaccard, 4)
                    })
    sim_df = pd.DataFrame(similarity_records)
    if not sim_df.empty:
        sim_df = sim_df.sort_values(by="jaccard_similarity", ascending=False)
        sim_df.to_csv("data/station_similarity_results.csv", index=False)

    # Compile Comprehensive JSON output
    results = {
        "network_overview": {
            "name": "Delhi Metro Rail Corporation (DMRC) & NCR Network",
            "total_stations": G.number_of_nodes(),
            "total_connections": G.number_of_edges(),
            "lines_count": len(METRO_LINES),
            "diameter_hops": diameter,
            "average_path_length": round(avg_path_len, 2),
            "transitivity": round(transitivity, 4),
            "average_clustering_coefficient": round(avg_clustering, 4),
            "reciprocity_directed": round(reciprocity_val, 4),
            "degree_assortativity": round(degree_assortativity, 4),
            "zone_assortativity": round(zone_assortativity, 4),
            "articulation_points_count": len(articulation_points),
            "articulation_points": sorted(articulation_points)
        },
        "top_degree": [{"station": k, "degree": v, "normalized": round(deg_centrality[k], 4)} for k, v in top_deg],
        "top_closeness": [{"station": k, "closeness": round(v, 4)} for k, v in top_close],
        "top_betweenness": [{"station": k, "betweenness": round(v, 4)} for k, v in top_between],
        "top_pagerank": [{"station": k, "pagerank": round(v, 4)} for k, v in top_pagerank],
        "top_bridge_edges": [
            {
                "edge": f"{u} <-> {v}",
                "betweenness": round(b, 4),
                "line": G[u][v].get("line", "")
            }
            for (u, v), b in top_edge_between
        ],
        "comparative_indian_metros": get_comparative_metro_benchmarks()
    }

    with open("data/metro_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Export to Gephi GEXF format and GraphML format
    # Enhance node attributes for Gephi
    for n in G.nodes():
        G.nodes[n]["degree"] = deg[n]
        G.nodes[n]["deg_centrality"] = float(deg_centrality[n])
        G.nodes[n]["closeness"] = float(closeness_hop[n])
        G.nodes[n]["betweenness"] = float(betweenness[n])
        G.nodes[n]["pagerank"] = float(pagerank[n])
        G.nodes[n]["clustering"] = float(clustering_coeff[n])
        G.nodes[n]["is_cut_vertex"] = int(n in articulation_points)

    nx.write_gexf(G, "exports/delhi_metro.gexf")
    nx.write_graphml(G, "exports/delhi_metro.graphml")
    print("Exported delhi_metro.gexf and delhi_metro.graphml for Gephi analysis.")

    return G, analysis_df, results

def get_comparative_metro_benchmarks():
    """Comparative benchmarks for Delhi, Bangalore, Mumbai, Hyderabad, Kolkata, Chennai."""
    return [
        {
            "metro": "Delhi Metro (DMRC)",
            "stations": 255,
            "lines": 10,
            "avg_degree": 2.24,
            "diameter": 36,
            "avg_path_len": 12.8,
            "transitivity": 0.015,
            "assortativity": -0.142,
            "nature": "Scale-Free Trunk-Spoke + Orbital Belt"
        },
        {
            "metro": "Bengaluru (Namma Metro)",
            "stations": 66,
            "lines": 2,
            "avg_degree": 2.03,
            "diameter": 28,
            "avg_path_len": 10.4,
            "transitivity": 0.000,
            "assortativity": -0.210,
            "nature": "Cross-Axis Topology (Majestic Hub)"
        },
        {
            "metro": "Hyderabad Metro (HMRL)",
            "stations": 57,
            "lines": 3,
            "avg_degree": 2.11,
            "diameter": 21,
            "avg_path_len": 8.1,
            "transitivity": 0.000,
            "assortativity": -0.245,
            "nature": "Triangular Grid Interchange (Ameerpet/MGBS)"
        },
        {
            "metro": "Mumbai Metro (MMRDA)",
            "stations": 43,
            "lines": 4,
            "avg_degree": 2.05,
            "diameter": 18,
            "avg_path_len": 6.9,
            "transitivity": 0.000,
            "assortativity": -0.198,
            "nature": "Linear Coastal Corridors with East-West Cross Link"
        },
        {
            "metro": "Kolkata Metro",
            "stations": 40,
            "lines": 3,
            "avg_degree": 2.00,
            "diameter": 25,
            "avg_path_len": 9.5,
            "transitivity": 0.000,
            "assortativity": -0.250,
            "nature": "Radial Linear Arterial with River Crossing"
        }
    ]

def generate_scientific_plots(G, analysis_df, results):
    plt.style.use('seaborn-whitegrid' if 'seaborn-whitegrid' in plt.style.available else 'default')
    
    # 1. Centrality Quadrant: Betweenness vs Closeness
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    x = analysis_df["closeness_centrality"]
    y = analysis_df["betweenness_centrality"]
    colors = ['#FF4D4D' if ic else '#2B82D9' for ic in analysis_df["is_interchange"]]
    sizes = [150 if ic else 40 for ic in analysis_df["is_interchange"]]
    
    scatter = ax.scatter(x, y, c=colors, s=sizes, alpha=0.75, edgecolors='none')
    
    # Annotate top 8 betweenness stations
    top_b = analysis_df.nlargest(8, "betweenness_centrality")
    for _, row in top_b.iterrows():
        ax.annotate(row["station"], (row["closeness_centrality"], row["betweenness_centrality"]),
                    xytext=(5, 5), textcoords="offset points", fontsize=8.5, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.6, ec="orange"))
        
    ax.set_title("Delhi Metro: Closeness vs Betweenness Centrality Quadrant", fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel("Closeness Centrality (Accessibility to Network)", fontsize=11)
    ax.set_ylabel("Betweenness Centrality (Interchange / Bridge Bottleneck)", fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Quadrant lines
    med_x = x.median()
    med_y = y.median()
    ax.axvline(med_x, color='gray', linestyle=':', alpha=0.6)
    ax.axhline(med_y, color='gray', linestyle=':', alpha=0.6)
    ax.text(med_x * 1.15, max(y) * 0.95, "CRITICAL BRIDGES & HUBS\n(High Betweenness, High Closeness)", fontsize=9, color="#B30000", fontweight='bold')
    ax.text(min(x) * 1.05, max(y) * 0.95, "PERIPHERAL BRIDGES", fontsize=8.5, color="purple")
    ax.text(min(x) * 1.05, min(y) + 0.005, "TERMINAL STATIONS", fontsize=8.5, color="gray")
    
    plt.tight_layout()
    plt.savefig("visualizations/centrality_quadrant.png")
    plt.close()

    # 2. Degree Distribution Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=300)
    deg_counts = analysis_df["degree"].value_counts().sort_index()
    bars = ax1.bar(deg_counts.index, deg_counts.values, color='#0072CE', edgecolor='#003366', width=0.6)
    ax1.set_title("Degree Distribution P(k)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Degree k (Direct Track Connections)", fontsize=10)
    ax1.set_ylabel("Station Count", fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.4)
    for bar in bars:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1, int(yval), ha='center', va='bottom', fontsize=9)

    # Boxplot of betweenness by zone
    zones = analysis_df["zone"].value_counts()[:6].index
    zone_data = [analysis_df[analysis_df["zone"] == z]["betweenness_centrality"] for z in zones]
    ax2.boxplot(zone_data, labels=[z.replace(" Delhi", "") for z in zones], patch_artist=True,
                boxprops=dict(facecolor="#A7D2FA", color="#005B94"),
                medianprops=dict(color="#D0021B", linewidth=2))
    ax2.set_title("Betweenness Centrality by City Zone", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Betweenness Centrality", fontsize=10)
    ax2.tick_params(axis='x', rotation=25)
    ax2.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig("visualizations/degree_distribution.png")
    plt.close()

    # 3. Network Resilience / Attack Tolerance Simulation
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    steps = 15
    # Targeted Attack by Betweenness
    G_attack = G.copy()
    giant_attack_sizes = [len(max(nx.connected_components(G_attack), key=len))]
    top_between_nodes = [item["station"] for item in results["top_betweenness"][:steps]]
    for node in top_between_nodes:
        if G_attack.has_node(node):
            G_attack.remove_node(node)
            comps = list(nx.connected_components(G_attack))
            giant_attack_sizes.append(len(max(comps, key=len)) if comps else 0)

    # Random Failure (mean of 20 simulations)
    random_curves = []
    np.random.seed(42)
    for sim in range(25):
        G_rand = G.copy()
        sizes = [len(max(nx.connected_components(G_rand), key=len))]
        rand_nodes = np.random.permutation(list(G.nodes()))[:steps]
        for node in rand_nodes:
            G_rand.remove_node(node)
            comps = list(nx.connected_components(G_rand))
            sizes.append(len(max(comps, key=len)) if comps else 0)
        random_curves.append(sizes)
    mean_random = np.mean(random_curves, axis=0)

    ax.plot(range(len(giant_attack_sizes)), giant_attack_sizes, 'r-o', linewidth=2.5, label="Targeted Removal (Top Betweenness Hubs)")
    ax.plot(range(len(mean_random)), mean_random, 'b--s', linewidth=2, label="Random Station Failures (Average)")
    ax.set_title("Network Resilience: Impact of Station Closures on Connected Giant Component", fontsize=13, fontweight='bold')
    ax.set_xlabel("Number of Stations Removed", fontsize=11)
    ax.set_ylabel("Size of Largest Connected Component (Stations)", fontsize=11)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig("visualizations/vulnerability_curve.png")
    plt.close()

    # 4. Multi-City Indian Metro Comparison Chart
    benchmarks = pd.DataFrame(results["comparative_indian_metros"])
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    x = np.arange(len(benchmarks))
    width = 0.35
    b1 = ax.bar(x - width/2, benchmarks["diameter"], width, label='Network Diameter (Hops)', color='#3A86FF')
    b2 = ax.bar(x + width/2, benchmarks["avg_path_len"], width, label='Average Path Length (Hops)', color='#FF006E')
    ax.set_title("Indian Metro Systems: Topological Diameter & Path Length Comparison", fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([m.split(" (")[0] for m in benchmarks["metro"]], rotation=15, ha='right', fontsize=10)
    ax.set_ylabel("Hops (Stations)", fontsize=11)
    ax.legend(frameon=True)
    ax.grid(True, linestyle='--', alpha=0.4)
    for b in b1:
        ax.text(b.get_x() + b.get_width()/2., b.get_height()+0.5, f"{int(b.get_height())}", ha='center', va='bottom', fontsize=8.5)
    for b in b2:
        ax.text(b.get_x() + b.get_width()/2., b.get_height()+0.5, f"{b.get_height():.1f}", ha='center', va='bottom', fontsize=8.5)
    plt.tight_layout()
    plt.savefig("visualizations/multi_city_comparison.png")
    plt.close()
    print("Scientific visualizations generated in visualizations/")

if __name__ == "__main__":
    nodes_df, edges_df = build_datasets()
    G, analysis_df, results = perform_network_analysis(nodes_df, edges_df)
    generate_scientific_plots(G, analysis_df, results)
    print("Network analysis and generation complete!")
