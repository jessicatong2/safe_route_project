# Safe Route Project

The Safe Route Project is intended to provide an additional possible layer of information to route calculations and recommendations and ultimately recommend safer routes for drivers. Most navigation apps and websites focus on providing the shortest and fastest routes for users, taking into consideration distance, time and traffic. However, there’s another factor that might be of higher importance for users depending on city, time and mode of transport: route safety. In cities where driving is the principal method of transportation drivers need a reliable route recommendation that will avoid dangerous areas and roads, especially when the driver follows blindly the routes that navigation systems provide.

This project takes into consideration two datasets:
1. Los Angeles Crime Data from 2010 to 2019: Used to obtain crime data and crime rates for crime risk calculation.
2. Los Angeles City Driving Network: Used to obtain the edges (streets), nodes (intersections), directions, distances and travel time.
Both datasets are included in a network analysis that is used to provide routes to get from point A to point B that not only take into consideration the length of the route, but also the added factor of crime rate.

It was very interesting to experiment with different ways of optimising the calculation of weights for each of the edges in the network. The weights were calculated by taking into consideration the length of each edge plus a crime risk. The crime risk takes into consideration the number of crimes near each edge, how relevant each crime is for driving risk and a factor, specified by the user, that represents how much of the crime risk should be taken into consideration for route calculation.
