"""
This module can be used to display 10 nearest film's locations
"""
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import folium
from math import sin, cos, atan2, sqrt, pi
import argparse

def get_data(path, year):
    """
    Returns list of lists, that includes film's name and location.
    Returns only films with appropriate year.
    e.g.
    [["American Psycho", "New York City, New York, USA"]]
    """
    with open(path, 'r', encoding='iso-8859-1', errors='ignore') as file:
        lines = file.readlines()
        start_ind = lines.index("==============\n")+1
        data = []
        for info in [line.split("\t") for line in lines[start_ind:-1]]:
            film = [el for el in info if el][0]
            location = [el for el in info if el][1].rstrip()
            if year in film[:film.index(" (")+6]:
                data.append([film[:film.index(year)-2].replace("'", "").replace('"', ""), location])
    return data

def find_coords(films_list):
    """
    Changes films_list, finding coordinates of every place.
    e.g.
    ['American Psycho', 'New York City, New York, USA']->['American Psycho', [40.7127281, -74.0060152]]
    """
    geolocator = Nominatim(user_agent="films_map")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.2)
    to_del = []
    for ind, line in enumerate(films_list):
        location = geolocator.geocode(line[1])
        while not location and line[1].count(",")>0:
            line[1] = ",".join(line[1].split(",")[1:])
            location = geolocator.geocode(line[1])
        if not location: 
            to_del.append(ind)
            continue
        films_list[ind][1] = [location.latitude, location.longitude]
    for ind in sorted(to_del, reverse=True):
        del films_list[ind]
        
def calculate_distance(film_location, your_location):
    """
    >>> calculate_distance([40.7127281, -74.0060152], [46.9758615, 31.9939666])
    7835935.921412968
    """
    lat1, lon1 = your_location[0], your_location[1]
    lat2, lon2 = film_location[0], film_location[1]
    Radius = 6371000
    fi1 = lat1 * pi / 180
    fi2 = lat2 * pi / 180
    dfi = (lat2 - lat1) * pi / 180
    dlam = (lon2 - lon1) * pi / 180
    haversin = sin(dfi/2)**2 + cos(fi1)*cos(fi2)*(sin(dlam/2)**2)
    c_value = 2 * atan2(sqrt(haversin), sqrt(1-haversin))
    return Radius * c_value

def form_addresses(data, your_location):
    """
    Forms a sorted dict of nearest 10 addresses
    >>> form_addresses([['"/Drive on NBCSN"', [36.2083012, -115.9839128]],
    ... ['"/Drive on NBCSN"', [36.4951365, -116.421881]],
    ... ['American Psycho', [40.7127281, -74.0060152]]], [24.4538352, 54.3774014])
    {'American Psycho': [[40.7127281, -74.0060152]], '"/Drive on NBCSN"': [[36.4951365, -116.421881], [36.2083012, -115.9839128]]}
    """
    films_sorted = sorted(data, key = lambda x : calculate_distance(x[1], your_location))[:10]
    films_dict = {}
    for line in films_sorted:
        films_dict[line[0]] = films_dict.get(line[0], []) + [line[1]]
    return films_dict

def create_map(films_dict, your_location):
    """
    Creates a map, pointing 10 nearest film's locations.
    Each film is new layer.
    """
    map = folium.Map(location=your_location, zoom_start=7)
    map.add_child(folium.Marker(location=your_location,
                                popup="You're here!",
                                icon=folium.Icon()))
    for film in films_dict:
        film_FG = folium.FeatureGroup(name = film)
        for coords in films_dict[film]:
            iframe = folium.IFrame(html=film, width=300, height=60)
            film_FG.add_child(folium.Marker(location=[coords[0], coords[1]],
                                            popup=folium.Popup(iframe),
                                            icon = folium.Icon(color="green")))
        map.add_child(film_FG)
    map.add_child(folium.LayerControl())
    map.save("Final.html")

def parse_args():
    """
    Creates argument parser with 4 arguments
    """
    parser = argparse.ArgumentParser(description=
        "Creates a map with 10 nearest films")
    parser.add_argument("year", type=str,
        help="")
    parser.add_argument("lat", type=float,
        help="latitude")
    parser.add_argument("lon", type=float,
        help="longitude")
    parser.add_argument("path", type=str,
        help="path to dataset")
    return parser.parse_args()

def main():
    """
    Main function
    """
    args = parse_args()
    data = get_data(args.path, args.year)
    find_coords(data)
    your_location = [args.lat, args.lon]
    sorted_addr = form_addresses(data, your_location)
    create_map(sorted_addr, your_location)
    print("Done!")

if __name__ == "__main__":
    main()
