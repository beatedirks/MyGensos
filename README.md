# Generic Civil Infrastructure Simulation
This repository showcases the python and SQL code of a generic simulation tool that was developed to allow the **simultaneous simulation of multiple civil infrastructure sectors**, whilst **accounting for their interdependencies**.

_Note: This work was created as part of a research project, whose results are still undergoing publication. Hence, this repository is not yet aimed at facilitating the usage of the developed simulation tool. If you are interested in using the framework, please contact the authors via beates_github@mailbox.org._

# What it's all about
A well functioning civil infrastructure system is the backbone of every prosperous society. But systems like the electricity grid and a countries transport system are very expensive to maintain and extend. Therefore, any government has to carefully optimize investments to guarantee the future well functioning of its infrastructre systems and at the same time to abide by further requirements, such as abiding to international green house gas reduction committments.

In order to achieve such sophisticated planning, government agencies rely on simulation and optimization tools. These are typically sector specific and are usually not designed to be used in interaction with the simulation tools of other sectors. The growing interconnectedness of infrastructure sectors (eg. electrification of the transport system, smart grids etc.) however requires simulations tools that allow simultaneous optimization of all sectors, whilst accounting for these interdependencies.

# Structure of the Implementation
In Main.py the user can trigger a series of modelruns and/or the visualization of their results.

## Modelruns
### Modelrun.py
For modelruns, the module Modelrun.py manages the different stages of a modelrun. Initially, infrastructure sector specific data will be read from individual sector databases and transformed into the required **generic format** and saved in respective input tables ("ISL_I_*"). 
### InfrastructureSystem.py
For smooth data access during the modelrun, all information will be temporarily stored in a cluster of objects that mimic the real structure and logic of infrastructure assets. InfrastructureSystem.py contains all respective classes and methods for this porpose.
### FlowNetwork.py
This module contains the actual simulation and optimization core of the framework. For each timestep in a given simulation, all infrastructure system information will be translated into a simple network. The capacities of infrastructure assets and demands for infrastructure services will be represented in the form of capacities of respective edges. 

This flow network is designed such that **the solution to the maximum flow problem will yield the optimized allocation of infrastructure services** onto given demands. 

Finally, **interdependecies amongst the different infrastructure sectors will be accounted for in itterative updating of capacity requirements of specific edges, based on the actual flows in other respective edges**.

## Modelrun Visualization
### Modelrun_Visualization.py
Modelrun_Visualization.py contains all functions needed for extracting modelrun  results from the database and display them with help of MatplotLib tools. For each simulation step a stacked representation of the analysed regions will allow insights into the predicted usage of infrastructure services, via colour coded symbols. A typical output will look like this:

![](Sample_Modelrun_Visualization_Output.png
)

- regional colour code - blue to red: how well are local demands fulfilled?
- colour coded arrows between regions - orange to red: how much service has been exchanged amongst the regions?
- colour coded arrows between regions - dark to light blue: how well have transport demands been fulfilled?
- grey and white columns indicate the extend to which capacity given assets are used
