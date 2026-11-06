import flet as ft

from project.application.build import building_the_application
from project.configuration.protocols import protocols as prot

print("USING protocols.py:", prot.__file__)
ft.app(target=building_the_application)
