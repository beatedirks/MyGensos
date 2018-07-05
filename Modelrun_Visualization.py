#fully supported by Matt Ives
import pyodbc
import process_region_shapes as prs
import shapefile as sf
import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Polygon, Arrow, Rectangle
import matplotlib.collections as mplc
import Modelrun_Objects as MO


def plot_regions(figure, regions, year):
    #if list_of_regions == 'all':
    #    list_of_regions = range(1,self.number_of_regions)
    (fig, ax) = figure
    patches = [] 
    region_colors = []       
    for region in regions:
        region_shape = regions[region]
        polygon = Polygon(region_shape.outline_coordinates, zorder = region_shape.zorder)
        patches.append(polygon)
        region_colors.append(region_shape.demand_fulfillment_values[str(year)])
        (x,y) = region_shape.center
        #plt.text(x, y, region_shape.name, ha="center", fontdict=dict(color='grey', size = 8, weight = 'bold'))
        plt.text(x, y, region_shape.text, ha="center", fontdict=dict(color='black', size = 8, weight = 'bold'))
        remaining_demand = region_shape.missing_supply_values[str(year)] 
        if remaining_demand > 0 :
             remaining_demand = "{:.1e}".format(remaining_demand)
             #plt.text(x, y-50000, remaining_demand, ha="center", fontdict=dict(color='grey', size = 8, weight = 'bold'))
             #plt.text(x, y-50000, remaining_demand, ha="center", fontdict=dict(color='grey', alpha = 0.4, size = 5, weight = 'bold'))
    cmap = matplotlib.cm.RdBu
    #norm = matplotlib.colors.Normalize(vmin=0, vmax=3)
    norm = matplotlib.colors.Normalize(vmin=-0.3, vmax=1.3)
    #p = mplc.PatchCollection(patches, cmap = cmap, norm=norm, edgecolor='grey', linewidth=1.0, zorder = region_shape.zorder)
    p = mplc.PatchCollection(patches, cmap = cmap, norm=norm, edgecolor='white', linewidth=1.0, zorder = 1, alpha = 0.5)
    p.set_array(np.array(region_colors))
    ax.add_collection(p)
    #create color bar
    #gradient = np.vstack((np.array([0,0]),np.array([0,3]))) # random array just to be able to plot an imshow, such that I can create a color bar - messy...^^
    #plt.imshow(gradient, aspect = 'auto', extent = (0, 3, 0, 1), cmap=cmap) # plot the image on effectively zero srface ;)
    #clb = plt.colorbar(ticks=[0, 1],  orientation='vertical', shrink=0.5)
    #clb.ax.set_yticklabels(['no supply', 'full supply'])
    return (fig,ax)

def plot_commodity_transfers(figure, transfers, year):
    (fig, ax) = figure
    patches = [] 
    arrow_colors = []
    for transfer in transfers:
        net_flow = transfers[transfer].transfers[str(year)]
        (ox, oy) = transfers[transfer].origin
        (dx, dy) = transfers[transfer].destination
        arrow = Arrow((ox+1000), (oy+1000), ((dx-ox)-1000), ((dy-oy)-1000),  width=30000, zorder = transfers[transfer].zorder)
        if net_flow > 0:    
            patches.append(arrow)
            arrow_colors.append(net_flow)
    try:
        vmax=max(arrow_colors)
        vmin=-max(arrow_colors)
    except:
        vmax=100
        vmin=0
    cmap = matplotlib.cm.Oranges
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    q = mplc.PatchCollection(patches, cmap = cmap, norm = norm, linewidth=0, zorder=2)
    q.set_array(np.array(arrow_colors))
    ax.add_collection(q)
    #create color bar
    #gradient = np.vstack((np.array([0,-vmax]),np.array([0,vmax]))) # random array just to be able to plot an imshow, such that I can create a color bar - messy...^^
    #plt.imshow(gradient, aspect = 'auto', extent = (0, 3, 0, 1), cmap=cmap) # plot the image on effectively zero srface ;)
    #clb = plt.colorbar(ticks=[0, vmax+1],  orientation='vertical', shrink=0.5)
    #clb.ax.set_yticklabels(['no transfer', 'maximum transfer'])
    return (fig,ax)

def plot_transports(figure, transports, year):
    (fig, ax) = figure
    patches = [] 
    arrow_colors = []
    for transport in transports:
        net_flow = transports[transport].transports[str(year)] 
        (ox, oy) = transports[transport].origin
        (dx, dy) = transports[transport].destination
        arrow = Arrow((ox+1000), (oy+1000), ((dx-ox)-1000), ((dy-oy)-1000),  width=30000, zorder = transports[transport].zorder)
        patches.append(arrow)
        arrow_colors.append(net_flow)
        if transports[transport].missing_supply_values[str(year)] > 0 :
            remaining_demand = "{:.1e}".format(transports[transport].missing_supply_values[str(year)])
            #plt.text((ox+dx)/2, (oy+dy)/2+150000, remaining_demand, ha="center", fontdict=dict(color='blue', size = 8, weight = 'bold', alpha = 0.6))
    try:
        vmax=max(arrow_colors)
        vmin=-max(arrow_colors)
    except:
        vmin=0
        vmax=100
    cmap = matplotlib.cm.Blues
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    q = mplc.PatchCollection(patches, cmap = cmap, norm = norm, linewidth=0, zorder = 2)
    q.set_array(np.array(arrow_colors))
    ax.add_collection(q)
    #create color bar
    #gradient = np.vstack((np.array([0,-vmax]),np.array([0,vmax]))) # random array just to be able to plot an imshow, such that I can create a color bar - messy...^^
    #plt.imshow(gradient, aspect = 'auto', extent = (0, 3, 0, 1), cmap=cmap) # plot the image on effectively zero srface ;)
    #clb = plt.colorbar(ticks=[0, vmax],  orientation='vertical', shrink=0.5)
    #clb.ax.set_yticklabels(['no transport', 'maximum transport'])
    return (fig,ax)

def plot_system_labels(figure, labels, plotting_offset, year):
    (fig, ax) = figure
    for (plot_position, labeltext) in labels:
        x = -70000
        y = 650000 + plot_position*plotting_offset
        plt.text(x, y, str(labeltext), ha="center", fontdict=dict(color='black', size = 8, weight = 'bold', horizontalalignment='left'))
    figure = (fig, ax)
    return figure

def plot_stacked_capacity_thumbs(figure, thumbs, year, norm):
    (fig, ax) = figure
    cap_thumbs = [] 
    thumb_colors = []
    edge_colors = []
    for submodel in thumbs:
        networks = thumbs[submodel][0]
        print networks
        for thumb in thumbs[submodel][1]:
            thumb_obj = thumbs[submodel][1][thumb]
            (x, y) = thumb_obj.coordinates
            y += 10000 # y offset to make tem hover slightly above the supply/demand vectors
            if norm == True:
                normfac = 0
                for network in networks: # calculate sum of maxcaps of all networks
                    normfac += thumb_obj.capacities[network + str(year)]
                normfac = 1.0*normfac/500000
            else:
                normfac = 1
            for network in networks:
                maxcap = thumb_obj.capacities[network + str(year)]
                supply = thumb_obj.supplies[network + str(year)]
                maxcap_rect = Rectangle((int(x), int(y)), 6000, 1.0*supply/normfac)
                thumb_colors.append('grey')
                edge_colors.append('none')
                supply_rect2 = Rectangle((int(x), int(y)+1.0*supply/normfac), 7000, 1.0*(maxcap-supply)/normfac)
                #supply_rect2 = Rectangle((int(x), int(y)), 6000, 1.0*maxcap/normfac)
                thumb_colors.append('none')
                edge_colors.append('black')
                cap_thumbs.append(maxcap_rect)
                cap_thumbs.append(supply_rect2) # unused capacity on top of used
                y += 1.0*maxcap/normfac # increase y by maxcap to make sure next thumb is stacked on top of these thumbs
    q = mplc.PatchCollection(cap_thumbs, linewidth = 0.5 , facecolors = thumb_colors, edgecolors = edge_colors, zorder = 3)
    ax.add_collection(q)
    return (fig,ax)

def plot_capacity_thumbs(figure, thumbs, year):
    (fig, ax) = figure
    cap_thumbs = [] 
    thumb_colors = []
    for thumb in thumbs:
        maxcap = thumbs[thumb].capacities[str(year)]
        supply = thumbs[thumb].supplies[str(year)]
        (x, y) = thumbs[thumb].coordinates
        maxcap_rect = Rectangle((int(x), int(y)), 7000, supply)
        thumb_colors.append('grey')
        #supply_rect1 = Rectangle((int(x+7000), int(y)), 7000, maxcap-supply)
        #thumb_colors.append('white')
        cap_thumbs.append(maxcap_rect)
        if maxcap > supply:
            supply_rect2 = Rectangle((int(x), int(y)+supply), 7000, maxcap-supply)
            thumb_colors.append('white')
        #cap_thumbs.append(supply_rect1) # unused capacity next to used
            cap_thumbs.append(supply_rect2) # unused capacity on top of used
    q = mplc.PatchCollection(cap_thumbs, linewidth = 1, facecolors = thumb_colors, alpha = 0.5, edgecolor = 'grey', zorder = 3)
    ax.add_collection(q)
    return (fig,ax)

def add_commodity_supply_over_demand(years, plot_position, plotting_offset,  keyservice, modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder):
    plotting_order = zorder
    # find submodel and region shapes
    cursor = cnxn.cursor()
    theSQL = 'SELECT submodel from "ISL_I_KeyServices" WHERE ks = ' + str("'") + str(keyservice) + str("'") + ' GROUP BY "ISL_I_KeyServices".submodel'
    (submodel, ) = list(cursor.execute(theSQL))[0]
    shapes = prs.load_regionshapes_from_file(local_strategies[submodel].shapefile)
    # derive demands and supplies from database and feed into shape objects
    #years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
    theSQL = 'SELECT demand_value, supply, simulation_year, region FROM "ISL_IO_FinalFlows_DemandFulfillments" WHERE modelrun_id = ' + str(modelrun_id) + ' AND \
        keyservice = ' + str("'") + keyservice + str("'") + ' AND current_forecast = ' + str("'current'") + ' AND simulation_year IN ' + str(years)
    cursor.execute(theSQL)
    new_line = cursor.fetchone()
    while new_line:
        [demand, supply, year, region] = new_line
        shape_name = str(keyservice) + '_' + str(region)
        shape_outline = shapes[str(region)].outline_coordinates
        if shape_name not in plotting_objects[0].keys():
            shape = prs.Region_Shape(shape_outline)
            shape.zorder = plotting_order
            shape.text = ''
            plotting_order += 1
            shape.offset_coordinates(plot_position, plotting_offset)
        else:
            shape = plotting_objects[0][shape_name]
        if demand != 0:
            shape.set_demand_fulfillment_values(1.0*supply/demand, year)
        else:
            shape.set_demand_fulfillment_values(1.0, year)
        shape.set_missing_supply_values(float(demand-supply), year)
        #shape_object.set_plotting_order(plot_position)
        plotting_objects[0][shape_name] = shape
        new_line = cursor.fetchone()
    return plotting_objects, plotting_order

def add_transport_supply_over_demand(years, plot_position, plotting_offset, keyservice, modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder):
    plotting_order = zorder
    transports = plotting_objects[2]
    # find submodel and region shapes
    cursor = cnxn.cursor()
    theSQL = 'SELECT submodel from "ISL_I_KeyServices" WHERE ks = ' + str("'") + str(keyservice) + str("'") + ' GROUP BY "ISL_I_KeyServices".submodel'
    (submodel, ) = list(cursor.execute(theSQL))[0]
    shapes = prs.load_regionshapes_from_file(local_strategies[submodel].shapefile)
    # derive demands and supplies from database and feed into shape objects
    #years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
    theSQL = 'SELECT demand, demand_value, supply, simulation_year, region FROM "ISL_IO_FinalFlows_DemandFulfillments" WHERE modelrun_id = ' + str(modelrun_id) + ' AND \
        keyservice = ' + str("'") + keyservice + str("'") + ' AND current_forecast = ' + str("'current'") + ' AND simulation_year IN ' + str(years)
    cursor.execute(theSQL)
    new_line = cursor.fetchone()
    while new_line:
        [demand_name, demand, supply, year, origin] = new_line
        destination = demand_name.split('_')[-1]
        transportname =  str(keyservice)+'_'+str(origin) + '_'+str(destination)
        if transportname not in transports.keys():
            [ox, oy] = shapes[str(origin)].center
            [dx, dy] = shapes[str(destination)].center
            dx = dx - (dx-ox)/2
            dy = dy- (dy-oy)/2
            origin_coord = [ox, oy]
            destination_coord = [dx, dy]
            transports[transportname] = prs.Transport(origin_coord, destination_coord)
            transports[transportname].zorder = plotting_order
            plotting_order += 1
            transports[transportname].offset_coordinates(plot_position, plotting_offset)
        if demand != 0:
            transports[transportname].add_transport(1.0*supply/demand, year)
        else:
            transports[transportname].add_transport(0, year)
        transports[transportname].add_missing_supply_values(demand, supply, year)
        new_line = cursor.fetchone()
    plotting_objects[2] = transports
    return plotting_objects, plotting_order

def add_intranet_commodity_transfers(years, plot_position, plotting_offset, network, modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder):
    plotting_order = zorder
    transfers = plotting_objects[1]
    # find submodel and region shapes
    cursor = cnxn.cursor()
    cursor_2 = cnxn.cursor()
    theSQL = 'SELECT submodel from "ISL_I_KeyServices" WHERE supplynw = ' + str("'") + str(network) + str("'") + ' GROUP BY "ISL_I_KeyServices".submodel'
    (submodel, ) = list(cursor.execute(theSQL))[0]
    shapes = prs.load_regionshapes_from_file(local_strategies[submodel].shapefile)
    # report transfers between regions
    #years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
    theSQL = 'SELECT simulation_year, origin, destination, total_flow FROM "ISL_IO_FinalFlows_DistributionNetworks" WHERE modelrun_id = ' + str(modelrun_id) + ' AND \
                network = ' + str("'")+ str(network) + str("'")+ ' AND cur_future_plan = ' + str("'current'") + ' AND simulation_year IN ' + str(years)
    cursor.execute(theSQL)
    new_line = cursor.fetchone()
    while new_line:
        [simulation_year, origin, destination, total_flow] = new_line
        theSQL = 'SELECT total_flow FROM "ISL_IO_FinalFlows_DistributionNetworks" WHERE (modelrun_id = ' + str(modelrun_id) + ' AND \
                    network = ' + str("'")+ str(network) + str("'")+ ' AND cur_future_plan = ' + str("'current'") + ' AND origin = ' + str(destination) + ' AND \
                    destination = ' + str(origin) + ' AND simulation_year = ' + str(simulation_year) + ')'  
        cursor_2.execute(theSQL)
        try:
            [total_flow_back] = cursor_2.fetchone()    
        except:
            total_flow_back = 0 
        net_flow = total_flow - total_flow_back  
        #if net_flow > 0:
        transfername =  str(network)+'_'+str(origin) + '_'+str(destination)
        if transfername not in transfers.keys():
            [ox, oy] = shapes[str(origin)].center
            [dx, dy] = shapes[str(destination)].center
            origin_coord = [ox, oy]
            destination_coord = [dx, dy]
            transfers[transfername] = prs.Transfer(transfername, origin_coord, destination_coord)
            transfers[transfername].zorder = plotting_order
            plotting_order += 1
            transfers[transfername].offset_coordinates(plot_position, plotting_offset)
            if transfername == 'Electricity_9_11':
                pass
                #print 'E_9_11 installed with origi  coords' + str(origin_coord) + ', ' + str(destination_coord) 
                #print 'E_9_11 installed with offset coords' + str(transfers[transfername].origin) + ', ' + str(transfers[transfername].destination)
        transfers[transfername].add_transfer(net_flow, simulation_year)
        if transfername == 'Electricity_9_11':
            pass
            #print 'E_9_11 - new transfer added ' + str(transfers[transfername].origin) + ', ' + str(transfers[transfername].destination)
        new_line = cursor.fetchone()
    plotting_objects[1] = transfers
    return plotting_objects, plotting_order

def add_internet_commodity_transfers(years, plot_position, plotting_offset, upORdown, keyservice, supplynetwork, modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder):
    plotting_order = zorder
    transfers = plotting_objects[1]
    # find submodel and region shapes
    cursor = cnxn.cursor()
    cursor_2 = cnxn.cursor()
    theSQL = 'SELECT submodel from "ISL_I_KeyServices" WHERE supplynw = ' + str("'") + str(supplynetwork) + str("'") + ' GROUP BY "ISL_I_KeyServices".submodel'
    (submodel, ) = list(cursor.execute(theSQL))[0]
    shapes = prs.load_regionshapes_from_file(local_strategies[submodel].shapefile)
    # report transfers between regions
    #years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
    theSQL = 'SELECT simulation_year, region, total_flow FROM "ISL_IO_FinalFlows_SuppliesByNetwork" WHERE modelrun_id = ' + str(modelrun_id) + ' AND \
                network = ' + str("'")+ str(supplynetwork) + str("'")+ ' AND keyservice = ' + str("'")+ str(keyservice) + str("'")+ ' AND cur_fut_plan = ' + str("'current'") + ' AND simulation_year IN ' + str(years)
    cursor.execute(theSQL)
    new_line = cursor.fetchone()
    while new_line:
        [simulation_year, origin, total_flow] = new_line
        transfername =  str(supplynetwork)+'_'+str(origin)+'_'+str(keyservice)
        if transfername not in transfers.keys():
            [ox, oy] = shapes[str(origin)].center
            if upORdown == 1:
                origin_coord = [ox, oy]
                destination_coord = [ox, oy+5*upORdown*plotting_offset/8]
            else:
                origin_coord = [ox, oy+4*upORdown*plotting_offset/8]
                destination_coord = [ox, oy+upORdown*plotting_offset]            
            new_transfer_object = prs.Transfer(transfername, origin_coord, destination_coord)
            new_transfer_object.zorder = plotting_order
            plotting_order += 1
            new_transfer_object.offset_coordinates(plot_position, plotting_offset)
            transfers[transfername] = new_transfer_object
        transfers[transfername].add_transfer(total_flow, simulation_year)
        new_line = cursor.fetchone()
    plotting_objects[1] = transfers
    return plotting_objects, plotting_order

def add_regions_with_names(years_string, plot_position, plotting_offset, shapefile, modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder):
    plotting_order = zorder
    # find region shapes
    cursor = cnxn.cursor()
    shapes = prs.load_regionshapes_from_file(shapefile)
    # derive demands and supplies from database and feed into shape objects
    for region in shapes.keys():
        shape_name = str(shapes[str(region)].name) + '_' + str(region)
        shape_outline = shapes[str(region)].outline_coordinates
        shape = prs.Region_Shape(shape_outline)
        shape.zorder = plotting_order
        plotting_order += 1
        shape.offset_coordinates(plot_position, plotting_offset)
        years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
        for year in years:
            shape.set_demand_fulfillment_values(1, year)
            shape.set_missing_supply_values(0, year)
            #shape.text = shape_name
            shape.text = ''
        #shape_object.set_plotting_order(plot_position)
        plotting_objects[0][shape_name] = shape
    return plotting_objects, plotting_order

def add_generation_asset_capacity_thumbs(years_string, plot_position, plotting_offset, network, modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, rescale_factor):
    plotting_order = zorder
    # find submodel and region shapes
    cursor = cnxn.cursor()
    theSQL = 'SELECT submodel from "ISL_I_KeyServices" WHERE supplynw = ' + str("'") + str(network) + str("'") + ' GROUP BY "ISL_I_KeyServices".submodel'
    (submodel, ) = list(cursor.execute(theSQL))[0]
    shapes = prs.load_regionshapes_from_file(local_strategies[submodel].shapefile)
    # derive caps and supplies from database and feed into shape objects
    #years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
    theSQL = 'SELECT SUM(total_flow), SUM(maxcap), region, simulation_year  FROM "ISL_IO_FinalFlows_GenerationAssets" WHERE modelrun_id = ' + str(modelrun_id) + ' AND \
        network = ' + str("'") + network + str("'") + ' AND cur_futur_plan = ' + str("'current'") + ' AND simulation_year IN ' + str(years_string) + '\
        GROUP BY region, simulation_year'
    cursor.execute(theSQL)
    new_line = cursor.fetchone()
    while new_line:
        [supply, maxcap, region, year] = new_line
        thumb_name = str(network) + '_' + str(region)
        if thumb_name not in plotting_objects[4].keys():
            [x, y] = shapes[str(region)].center
            coordinates = [x-10000, y+10000]
            cap_thumb = prs.Asset_Capacity_And_Usage(coordinates)
            cap_thumb.zorder = plotting_order
            plotting_order += 1
            cap_thumb.offset_coordinates(plot_position, plotting_offset)
        else:
            cap_thumb = plotting_objects[4][thumb_name]
        try:
            cap_thumb.set_values(int(maxcap)*rescale_factor, int(supply)*rescale_factor, year)
        except:
            cap_thumb.set_values(0, 0, year)
            print 'error: maxcap and supply of assets ' +  str(thumb_name) + ' not found for year ' + str(year)
        plotting_objects[4][thumb_name] = cap_thumb
        new_line = cursor.fetchone()
    return plotting_objects, plotting_order

def add_stacked_transmission_capacity_thumbs(years_string, plot_position, plotting_offset, submodel, modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, rescale_factor, order_of_networks):
    plotting_order = zorder
    # find region shapes
    cursor = cnxn.cursor()
    shapes = prs.load_regionshapes_from_file(local_strategies[submodel].shapefile)
    years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
    theSQL = 'SELECT network, SUM(total_flow), SUM(maxcap), origin, destination, simulation_year  FROM "ISL_IO_FinalFlows_DistributionNetworks" WHERE modelrun_id = ' + str(modelrun_id) + ' AND \
        submodel = ' + str("'") + submodel + str("'") + ' AND cur_future_plan = ' + str("'current'") + ' AND simulation_year IN ' + str(years_string) + '\
        GROUP BY network, origin, destination, simulation_year'
    cursor.execute(theSQL)
    new_line = cursor.fetchone()
    while new_line:
        [network, supply, maxcap, origin, destination, year] = new_line
        if submodel not in plotting_objects[5].keys():
            plotting_objects[5][submodel] = [[],{}]
            plotting_objects[5][submodel][0] = order_of_networks
        #if network not in plotting_objects[5][submodel][0]:
            #plotting_objects[5][submodel][0].append(network)
        thumb_name = str(submodel) + '_' + str(origin) + '_' + str(destination)
        if thumb_name not in plotting_objects[5][submodel][1].keys():
            [ox, oy] = shapes[str(origin)].center
            [dx, dy] = shapes[str(destination)].center
            coordinates = [ox+(dx-ox)/3, oy+(dy-oy)/3]
            cap_thumb = prs.Stacked_Asset_Capacity_And_Usage(coordinates, order_of_networks)
            cap_thumb.zorder = plotting_order
            plotting_order += 1
            cap_thumb.offset_coordinates(plot_position, plotting_offset)
        else:
            cap_thumb = plotting_objects[5][submodel][1][thumb_name]
        try:
            cap_thumb.set_values(network, int(maxcap)*rescale_factor, int(supply)*rescale_factor, year)
            if network not in cap_thumb.networks:
                cap_thumb.networks.append(network)
        except:
            cap_thumb.set_values(0, 0, year)
            print 'error: maxcap and supply of assets ' +  str(thumb_name) + ' not found for year ' + str(year)
        plotting_objects[5][submodel][1][thumb_name] = cap_thumb
        new_line = cursor.fetchone()
    return plotting_objects, plotting_order

def add_transmission_asset_capacity_thumbs(years_string, plot_position, plotting_offset, network, modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, rescale_factor):
    plotting_order = zorder
    # find submodel and region shapes
    cursor = cnxn.cursor()
    theSQL = 'SELECT submodel from "ISL_I_KeyServices" WHERE supplynw = ' + str("'") + str(network) + str("'") + ' GROUP BY "ISL_I_KeyServices".submodel'
    (submodel, ) = list(cursor.execute(theSQL))[0]
    shapes = prs.load_regionshapes_from_file(local_strategies[submodel].shapefile)
    years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
    theSQL = 'SELECT SUM(total_flow), SUM(maxcap), origin, destination, simulation_year  FROM "ISL_IO_FinalFlows_DistributionNetworks" WHERE modelrun_id = ' + str(modelrun_id) + ' AND \
        network = ' + str("'") + network + str("'") + ' AND cur_future_plan = ' + str("'current'") + ' AND simulation_year IN ' + str(years_string) + '\
        GROUP BY origin, destination, simulation_year'
    cursor.execute(theSQL)
    new_line = cursor.fetchone()
    while new_line:
        [supply, maxcap, origin, destination, year] = new_line
        thumb_name = str(network) + '_' + str(origin) + '_' + str(destination)
        if thumb_name not in plotting_objects[4].keys():
            [ox, oy] = shapes[str(origin)].center
            [dx, dy] = shapes[str(destination)].center
            coordinates = [ox+(dx-ox)/4, oy+(dy-oy)/4]
            cap_thumb = prs.Asset_Capacity_And_Usage(coordinates)
            cap_thumb.zorder = plotting_order
            plotting_order += 1
            cap_thumb.offset_coordinates(plot_position, plotting_offset)
        else:
            cap_thumb = plotting_objects[4][thumb_name]
        try:
            cap_thumb.set_values(int(maxcap)*rescale_factor, int(supply)*rescale_factor, year)
        except:
            cap_thumb.set_values(0, 0, year)
            print 'error: maxcap and supply of assets ' +  str(thumb_name) + ' not found for year ' + str(year)
        plotting_objects[4][thumb_name] = cap_thumb
        new_line = cursor.fetchone()
    return plotting_objects, plotting_order

def create_figures(modelrun_params, global_strategy, plotting_objects, min_plot_position, max_plot_position, plotting_offset, modelrun_id):
    for year in np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval):
        filename = 'modelrun_doc_images/' + str(modelrun_id) + '_SoS_' + str(year) + '.png'
        (fig, ax) = plt.subplots(figsize=(8,10))
        #fig = plt.figure(figsize = (10, 7))
        #ax = plt.Axes(fig)
        figure = (fig, ax)
        #plt.xlim(-200000, 600000)
        plt.xlim(-100000, 600000)
        plt.ylim(min_plot_position*plotting_offset, 1000000+max_plot_position*plotting_offset)   
        #ax.get_xaxis().set_visible(False)
        #ax.get_yaxis().set_visible(False)   
        plt.axis('off')  
        if plotting_objects[2]:
            figure = plot_transports(figure, plotting_objects[2], year)
        if plotting_objects[1]:
            figure = plot_commodity_transfers(figure, plotting_objects[1], year)
        if plotting_objects[0]:
            figure = plot_regions(figure, plotting_objects[0], year) 
        if plotting_objects[3]:
            figure = plot_system_labels(figure, plotting_objects[3], plotting_offset, year)
        if plotting_objects[4]:
            figure = plot_capacity_thumbs(figure, plotting_objects[4], year)
        if plotting_objects[5]:
            figure = plot_stacked_capacity_thumbs(figure, plotting_objects[5], year, False)
        plt.title(filename)      
        #plt.show()
        plt.savefig(filename)
        #plt.close()
        
def visualize_modelruns(list_of_modelruns, cnxn):
    for modelrun in list_of_modelruns:
        run_visualization(modelrun, cnxn)

def run_visualization(modelrun_id, cnxn):
    cursor = cnxn.cursor()
    # load modelrun information from model run table:
    plotting_offset = 800000
    cursor.execute('select global_strategy_id, scenario_id, submodel_portfolio_id, startyear, endyear, "Notes", no_build from "ISL_S_ModelRuns" where modelrun_id = ' + str(modelrun_id))
    (global_strategy_id, global_scenario_id, submodel_portfolio_id, start_year, end_year, Notes, no_build) = cursor.fetchone()
    global_strategy = MO.Global_Strategy(global_strategy_id, cnxn)
    local_strategies = MO.Local_Strategies(submodel_portfolio_id, cnxn)
    modelrun_params = MO.Modelrun_Params(start_year, end_year, no_build) 
    years = tuple(np.arange(modelrun_params.start_year, modelrun_params.end_year, global_strategy.planning_interval))
    if len(years) == 1:
        year = years[0]
        years_string = '(' + str(year) + ')'
    else:
        years_string = str(years)
    # prepare region shapes
    # process shapefile if not yet done:
    #prs.process_region_shapes('water companies/water companies.shx', 'GNE_GOR_shapes', [(11,21),(9,4),(7,2),(8,1)], [(11, 'Scotland'), (9, 'North East'), (8, 'North West'), (7, 'Yorkshire')])

    # specify what to plot
    zorder = 0
    region_objects = {}
    transfer_objects = {}
    transport_objects = {}
    labels = []
    capacity_thumbs = {}
    stacked_cap_thumbs = {}
    plotting_objects = [region_objects, transfer_objects, transport_objects, labels, capacity_thumbs, stacked_cap_thumbs]
    #plotting_objects[3].append((-4, 'Geographical aggregation into GORs'))
    plotting_objects, zorder = add_regions_with_names(years_string, -1, plotting_offset, 'GNE_GOR_shapes', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    #plotting_objects[3].append((-4, 'local transport supply/demand'))
    #plotting_objects, zorder = add_commodity_supply_over_demand(years, -4, plotting_offset, 'localtransport', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    #plotting_objects[3].append((-1, 'interzone transport'))
    #plotting_objects[3].append((-0.5, 'Road and Rail'))
    #plotting_objects[3].append((-0.75, 'RailD, RailE, RoadFCar, RoadECar'))
    #plotting_objects, zorder = add_transport_supply_over_demand(years_string, -1, plotting_offset, 'transport', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    #plotting_objects, zorder = add_stacked_transmission_capacity_thumbs(years_string, -1, plotting_offset, 'Transport', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 0.4, ['RailDiesel', 'RailElectric', 'RoadFuelCar', 'RoadElectricCar'])
    #plotting_objects[3].append((-1.5, 'RoadElectricCar capacity usage'))
    #plotting_objects, zorder = add_transport_supply_over_demand(years_string, -3, plotting_offset, 'transport', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    #plotting_objects, zorder = add_transmission_asset_capacity_thumbs(years_string, -3, plotting_offset, 'RoadElectricCar', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 1)
    #plotting_objects[3].append((-1.75, 'RailDiesel capacity usage'))
    #plotting_objects, zorder = add_transport_supply_over_demand(years_string, -2, plotting_offset, 'transport', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    #plotting_objects, zorder = add_transmission_asset_capacity_thumbs(years_string, -2, plotting_offset, 'RailDiesel', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 1)
    #plotting_objects[3].append((-1.25, 'RailElectric capacity usage'))
    #plotting_objects, zorder = add_transport_supply_over_demand(years_string, -1, plotting_offset, 'transport', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    #plotting_objects, zorder = add_transmission_asset_capacity_thumbs(years_string, -1, plotting_offset, 'RailElectric', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 1)
    plotting_objects[3].append((-1, 'interregional transport supply/demand'))
    plotting_objects[3].append((-0.5, 'Road and Rail capacity usage'))
    plotting_objects[3].append((-0.75, 'RailDiesel, RailElectric, RoadFuelCar, RoadElectricCar'))
    plotting_objects, zorder = add_transport_supply_over_demand(years_string, -1, plotting_offset, 'transport', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects, zorder = add_stacked_transmission_capacity_thumbs(years_string, -1, plotting_offset, 'Transport', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 0.4, ['RailDiesel', 'RailElectric', 'RoadFuelCar', 'RoadElectricCar'])
    plotting_objects[3].append((1, 'electricity'))
    plotting_objects[3].append((1.2, 'Electricity'))
    plotting_objects, zorder = add_intranet_commodity_transfers(years_string, 1, plotting_offset, 'Electricity', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects, zorder = add_commodity_supply_over_demand(years_string, 1, plotting_offset, 'electricity', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects, zorder = add_generation_asset_capacity_thumbs(years_string, 1, plotting_offset, 'Electricity', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 1.5)
    plotting_objects[3].append((1.5, 'Electricity for heat'))
    plotting_objects[3].append((2, 'heat usage from synergy * 10'))
    plotting_objects[3].append((2.2, 'Gas for heat'))
    plotting_objects, zorder = add_internet_commodity_transfers(years_string, 1, plotting_offset, 1, 'heat', 'Electricity', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects, zorder = add_commodity_supply_over_demand(years_string, 2, plotting_offset, 'heat', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects, zorder = add_generation_asset_capacity_thumbs(years_string, 2, plotting_offset, 'Heat', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 15)
    plotting_objects, zorder = add_internet_commodity_transfers(years_string, 3, plotting_offset, -1, 'heat', 'Gas', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects[3].append((3, 'gas'))
    plotting_objects[3].append((3.2, 'Gas'))
    plotting_objects, zorder = add_commodity_supply_over_demand(years_string, 3, plotting_offset, 'gas', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects, zorder = add_generation_asset_capacity_thumbs(years_string, 3, plotting_offset, 'Gas', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 1.5)
    plotting_objects, zorder = add_intranet_commodity_transfers(years_string, 3, plotting_offset, 'Gas', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects[3].append((4, 'water supply/demand'))
    plotting_objects[3].append((4.2, 'Water transfers'))
    plotting_objects, zorder = add_commodity_supply_over_demand(years_string, 4, plotting_offset, 'water', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    plotting_objects, zorder = add_generation_asset_capacity_thumbs(years_string, 4, plotting_offset, 'Water', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 0.3)
    plotting_objects, zorder = add_intranet_commodity_transfers(years_string, 4, plotting_offset, 'Water', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder)
    #plotting_objects, zorder = add_transmission_asset_capacity_thumbs(years_string, 4, plotting_offset, 'Water', modelrun_id, modelrun_params, global_strategy, local_strategies, plotting_objects, cnxn, zorder, 0.3)
    create_figures(modelrun_params, global_strategy, plotting_objects, -3, 4.5, plotting_offset, modelrun_id)        
    print str(zorder)




