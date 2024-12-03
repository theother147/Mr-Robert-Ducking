import sys 
import pkg_resources 
import re 
 
def get_top_level_packages(): 
    with open('requirements.txt') as f: 
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')] 
    packages = [] 
    for req in requirements: 
