import pandas as pd
import networkx as nx
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, Polygon
import pyproj
import requests
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
from tqdm import tqdm
from ast import literal_eval
import pickle

class RouteModel:
    import pickle
    from ast import literal_eval
    
    def __init__(self, start_latlong, end_latlong, route_safety_importance):
        '''
        
        
        Inputs
        ----------------
        start_latlong: tuple, (lat, long) signifying route start location.
        end_latlong: tuple, (lat, long) signifying route end location.
        route_safety_importance: float, between 0.0 and 1.0, 0.0 for no importance to safety, 1.0 for full safety importance.
        '''
        self.safety = route_safety_importance
        self.start = start_latlong
        self.end = end_latlong
        self.center = ((self.start[0]+self.end[0])/2, (self.start[1]+self.end[1])/2)
        
        # Use the latitude and longitude of the start and end points to create a boundary box that uses the further 
        # north, south, east and west latitude and longitude plus a proportional buffer to create a smaller graph for
        # displaying the routes calculated
        
        if self.start[0]<self.end[0]:
            s_edge = self.start[0] - (self.end[0]-self.start[0])*0.1
            n_edge = self.end[0] + (self.end[0]-self.start[0])*0.1
        else:
            n_edge = self.start[0] + (self.start[0]-self.end[0])*0.1
            s_edge = self.end[0] - (self.start[0]-self.end[0])*0.1
        if self.start[1]<self.end[1]:
            w_edge = self.start[1] - (self.end[1]-self.start[1])*0.1
            e_edge = self.end[1] + (self.end[1]-self.start[1])*0.1
        else:
            e_edge = self.start[1] + (self.start[1]-self.end[1])*0.1
            w_edge = self.end[1] - (self.start[1]-self.end[1])*0.1 

        self.bbox = (n_edge,s_edge,e_edge,w_edge)
        
        # Create a geometry using the start, end and center points used as inputs
        geom = [Point(xy) for xy in [self.start, self.end, self.center]]
        # Use the geometry as the data to create a GeoDataFrame
        gdf = gpd.GeoDataFrame(geometry=geom,crs={'init':'epsg:4326'})
        gdf.index = ['start', 'end', 'center']
        
        # Instantiate Proj objects to transform latitude,longitude coordinates to x,y coordinates of the start, center and end
        # points geometry
        wgs84 = pyproj.Proj(init='epsg:4326')
        utm10s = pyproj.Proj(init='epsg:32611')
        utf_coords = []
        for lat, long in [x.coords[0] for x in gdf.geometry]:
            c = pyproj.transform(wgs84, utm10s, long, lat)
            utf_coords.append(Point(c))

        # Create a GeoDataFrame using the start, center and end points x,y coordinates as data
        gdf = gpd.GeoDataFrame(geometry=utf_coords,crs={'init':'epsg:32611'})
        gdf.index = ['start', 'end', 'center']
        
        # Calculate the distances from each point to the others in the gdf GeoDataFrame and add the distances as data in new
        # columns in the gdf GeoDataFrame
        s_dist = []
        e_dist = []
        c_dist = []

        for x in gdf.index:
            for y in gdf.index:
                if x=='start':
                    s_dist.append(gdf.loc[x, 'geometry'].distance(gdf.loc[y, 'geometry']))
                elif x=='end':
                    e_dist.append(gdf.loc[x, 'geometry'].distance(gdf.loc[y, 'geometry']))
                else:
                    c_dist.append(gdf.loc[x, 'geometry'].distance(gdf.loc[y, 'geometry']))

        gdf['dist_to_start'] = s_dist
        gdf['dist_to_end'] = e_dist
        gdf['dist_to_center'] = c_dist
        
        # Calculate a reasonable distance from the center point to create an extent for a smaller map for route visualization
        self.map_extent = gdf['dist_to_center']['start'] + 500
        
        
        self.weights = pd.read_csv('./LA_weights.csv')
        self.weights.edge = [literal_eval(x) for x in self.weights.edge]
        
        with open('la_graph.pkl', 'rb') as f:
            self.G = pickle.load(f)
    
        for start_, end_ in list(self.weights.edge):
            self.G[start_][end_][0]['weight']=(self.G[start_][end_][0]['crime_risk']*self.safety) + self.G[start_][end_][0]['length']
    
    def plot_map_extent(self):
    # Plots the reduced graph using the created boundary box with the start and end points
        fig, ax = ox.plot_graph(self.G,bbox=self.bbox, fig_height=10)
        plt.show()
            
    def plot_shortest_route(self):
    # Calculates the shortest route from start point to end point taking only the length of the edges as the weight
    # and plots the route on the reduced graph using the boundary box
        orig_node = ox.get_nearest_node(self.G, self.start)
        dest_node = ox.get_nearest_node(self.G, self.end)
        route = nx.shortest_path(self.G, orig_node, dest_node, weight='length')
        #print('Path Length:',nx.shortest_path_length(self.G, orig_node, dest_node, weight='length'))
        fig, ax = ox.plot_graph_route(self.G, route,bbox=self.bbox, node_size=0, fig_height=15)
        plt.show()      
    
    def plot_safety_weighted_route(self):
    # Calculates the shortest route from start point to end point using the safety risk, safety factor and length as 
    # the weight and plots the route on the reduced graph using the boundary box
        
        orig_node = ox.get_nearest_node(self.G, self.start)
        dest_node = ox.get_nearest_node(self.G, self.end)
        
        route = nx.shortest_path(self.G, 
                                 orig_node, 
                                 dest_node, 
                                 weight='weight')
        #print('Path Length:',nx.shortest_path_length(self.G, orig_node, dest_node, weight='weight'))
        fig, ax = ox.plot_graph_route(self.G,route, bbox=self.bbox,node_size=0, fig_height=15)
        plt.show()
        
    def plot_two_routes(self):
    # Plots the shortest route and safest route on the same map for comparison purposes and prints the total length of
    # both routes
        
        orig_node = ox.get_nearest_node(self.G, self.start)
        dest_node = ox.get_nearest_node(self.G, self.end)
        route1 = nx.shortest_path(self.G, orig_node, dest_node, weight='length')
        route2 = nx.shortest_path(self.G, 
                                 orig_node, 
                                 dest_node, 
                                 weight='weight')

        
        print('Shortest Path Length:',nx.shortest_path_length(self.G, orig_node, dest_node, weight='length'))
        print('Safer Path Length:',nx.shortest_path_length(self.G, orig_node, dest_node, weight='weight'))
              
        rc1 = ['r'] * (len(route1) - 1)
        rc2 = ['b'] * len(route2)
        rc = rc1 + rc2
        nc = ['r', 'r', 'b', 'b']

        # plot the routes
        fig, ax = ox.plot_graph_routes(self.G, [route1, route2],bbox=self.bbox,
                                       route_color=rc, orig_dest_node_color=nc, node_size=0,fig_height=15)