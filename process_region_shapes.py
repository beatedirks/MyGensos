
import shapefile as sf
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Polygon, Arrow
import matplotlib.collections as mplc

def read_shapefile(filename):
    gbgeom = sf.Reader(filename)
    shapes = gbgeom.shapes()
    shape_dict = {}
    i = 0
    for shape in shapes:
        i += 1
        shape_points = remove_bad_points(shape.points)
        shape_dict[str(i)] = Region_Shape(shape_points)
    return shape_dict

def remove_bad_points(shape_points):
    new_shape_points = []
    for i in range(len(shape_points)-1):
        if ((abs(shape_points[i][0]-shape_points[i+1][0]) < 10000) and (abs(shape_points[i][1]-shape_points[i+1][1]) < 10000)):
            new_shape_points.append(shape_points[i])
        else: 
            return new_shape_points
    if new_shape_points == []:
        print 'stop'
    return new_shape_points

def save_regionshapes_to_file(shape_dict, filename):
    filehandler = open(filename, 'w')
    pickle.dump(shape_dict, filehandler)

def load_regionshapes_from_file(filename):
    filehandler = open(filename, 'r')
    shape_dict = pickle.load(filehandler)
    return shape_dict

def reindex_regions(shape_dict, region_reindexing):
    new_shape_dict = {}
    for (new, old) in region_reindexing:
        new_shape_dict[str(new)] = shape_dict[str(old)]
    return new_shape_dict

def add_region_names(shape_dict, region_names):
    for (regionindex, regionname) in region_names:
        shape_dict[str(regionindex)].name = regionname
    return shape_dict

def process_region_shapes(inputfilename, outputfilename, list_for_reindexing, list_for_naming):
    shape_dict = read_shapefile(inputfilename)
    shape_dict = reindex_regions(shape_dict, list_for_reindexing)
    shape_dict = add_region_names(shape_dict, list_for_naming)
    save_regionshapes_to_file(shape_dict, outputfilename)


class Region_Shapes():

    def __init__(self):
        self.region_shapes = {}
        self.number_of_regions = 0 # default

    def add_regionshapes(self, shape_dict):
        for region in shape_dict:
            if region in self.region_shapes.keys():
                print 'Warning: Region shape with name ' + str(region) + ' already exists and will be over written.'
            self.region_shapes[region] = shape_dict[region] 
        self.number_of_regions = len(self.region_shapes.keys())

    def process_region_shapes(self, shapefilename, savefilename, reindexing_list):
        shape_dict = self.read_shapefile(shapefilename)
        new_shape_dict = self.reindex_regions(shape_dict, reindexing_list)
        self.save_regionshapes_to_file(new_shape_dict, savefilename)
        
    def get_shape(self, id):
        return self.region_shapes[str(id)]   

class Region_Shape():

    def __init__(self, outline_coordinates):
        self.outline_coordinates = outline_coordinates
        self.define_center()
        self.demand_fulfillment_values = {} 
        self.missing_supply_values = {}
        self.transfers = {}

    def define_center(self):
        xmin = min((a) for (a,b) in self.outline_coordinates)
        xmax = max((a) for (a,b) in self.outline_coordinates)
        ymin = min((b) for (a,b) in self.outline_coordinates)
        ymax = max((b) for (a,b) in self.outline_coordinates)
        xcenter = xmin + (xmax-xmin)/2
        ycenter = ymin + (ymax-ymin)/2
        self.center = [xcenter, ycenter]

    def set_demand_fulfillment_values(self, value, year):
        self.demand_fulfillment_values[str(year)] = value

    def set_missing_supply_values(self, value, year):
        self.missing_supply_values[str(year)] = float(value)

    def offset_coordinates(self, plot_position, plotting_offset):
        offset = plot_position*plotting_offset
        new_coordinates = []
        for (x,y) in self.outline_coordinates:
            new_coordinates.append((x, y+offset))
        self.outline_coordinates = new_coordinates
        self.define_center()

    def add_transfer(self, origin, destination, value, year):
        if str(year) in self.transfers.keys():
            self.transfers[str(year)].append((origin, destination, value))
        else:
            self.transfers[str(year)] = [(origin, destination, value)]
    
    def set_plotting_order(self, plot_position):
        self.zorder = plot_position*3

class Transfer():

    def __init__(self, transfername, origin_coord, destination_coord):
        self.name = transfername
        self.origin = origin_coord
        self.destination = destination_coord
        self.transfers = {} 
        #print 'new transferobject: ' + str(transfername) + ', ' + str(origin_coord) + ', ' + str(destination_coord)

    def add_transfer(self, value, year):
        self.transfers[str(year)] = value

    def offset_coordinates(self, plotting_position, plotting_offset):
        oy = self.origin[1] + plotting_position*plotting_offset
        dy = self.destination[1] + plotting_position*plotting_offset
        self.origin[1] = oy
        self.destination[1] = dy
        #print 'NC for ' + str(self.name) + ': ' + str(self.origin) + ' ' + str(self.destination)

class Transport():

    def __init__(self, origin_coord, destination_coord):
        self.origin = origin_coord
        self.destination = destination_coord
        self.transports = {} 
        self.missing_supply_values = {}
        

    def add_transport(self, value, year):
        self.transports[str(year)] = value

    def offset_coordinates(self, plotting_position, plotting_offset):
        self.origin[1] += plotting_position*plotting_offset
        self.destination[1] += plotting_position*plotting_offset

    def add_missing_supply_values(self, demand, supply, year):
        self.missing_supply_values[str(year)] = float(demand-supply)


class Asset_Capacity_And_Usage():

    def __init__(self, coordinates):
        self.capacities = {}
        self.supplies = {}
        self.coordinates = coordinates

    def set_values(self, capacity, supply, year):
        self.capacities[str(year)] = capacity
        self.supplies[str(year)] = supply

    def offset_coordinates(self, plot_position, plotting_offset):
        offset = plot_position*plotting_offset
        (x,y) = self.coordinates
        self.coordinates = (x, y+offset)

    def set_plotting_order(self, plot_position):
        self.zorder = plot_position*3


class Stacked_Asset_Capacity_And_Usage():

    def __init__(self, coordinates, order_of_networks):
        self.capacities = {}
        self.supplies = {}
        self.coordinates = coordinates
        self.networks = order_of_networks

    def set_values(self, network, capacity, supply, year):
        self.capacities[network + str(year)] = capacity
        self.supplies[network + str(year)] = supply

    def offset_coordinates(self, plot_position, plotting_offset):
        offset = plot_position*plotting_offset
        (x,y) = self.coordinates
        self.coordinates = (x, y+offset)

    def set_plotting_order(self, plot_position):
        self.zorder = plot_position*3
