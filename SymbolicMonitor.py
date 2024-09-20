import os
from collections import defaultdict
from typing import List, Dict

import pandas as pd
import pickle
import SG_Primitives as P
import SG_Utils as utils
import Property
from SymbolicEntity import SymbolicEntity, ConcreteEntity
from SymbolicProperty import ConcreteProperty, SymbolicProperty, UnboundEntityError
from symbolic_properties import all_symbolic_properties
from time import time
from PIL import Image
from functools import partial
from pathlib import Path
import json


class SymbolicViolation:
    def __init__(self, property_name: str, violation_time, initial_frame,
                 entity_mapping: Dict[SymbolicEntity, ConcreteEntity],
                 data_history, name_history, frames, ego_id):
        self.property_name = property_name
        self.violation_time = violation_time
        self.entity_mapping = entity_mapping
        self.initial_frame = initial_frame
        self.data_history = data_history
        self.name_history = name_history
        self.frames = frames
        self.ego_id = ego_id

    def to_json(self, save_file):
        data = {
            'entity_mapping': {symbolic_entity.name: concrete_entity.entity_id if concrete_entity is not None else None
                               for symbolic_entity, concrete_entity in self.entity_mapping.items()},
            'violation_time': self.violation_time,
            'initial_frame': self.initial_frame,
            'ego_id': self.ego_id,
            'name_history': [(frame, {symbolic_entity.name: name
                                      for symbolic_entity, name in names.items()})
                             for frame, names in self.name_history.items()],
            'data_history': [(frame, {k: v if type(v) != UnboundEntityError else None for k, v in hist.items()})
                             for frame, hist in self.data_history.items()]
        }
        with open(save_file, 'w') as f:
            json.dump(data, f)

class SymbolicMonitor:
    def __new__(cls, *args, **kwargs):
        if (len(args) > 0 or len(kwargs) > 0) and hasattr(cls,
                                                          'monitor_instance'):
            del cls.monitor_instance

        if not hasattr(cls, 'monitor_instance'):
            cls.monitor_instance = super(SymbolicMonitor, cls).__new__(cls)
            cls.monitor_instance.initialize(*args, **kwargs)
        return cls.monitor_instance

    def initialize(self, log_path, route_path):
        self.symbolic_properties: List[SymbolicProperty] = all_symbolic_properties
        self.concrete_properties: List[ConcreteProperty] = []
        self.previous_concrete = []
        self.timestep = 0

        self.violations = defaultdict(list)
        self.ego_id = None

        # Create log directory
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        # Create route directory
        self.route_path = self.log_path / route_path
        self.route_path.mkdir(parents=True, exist_ok=True)
        self.iterations_per_frame = {}

    # def hard_reset(self):
    #     """
    #     Hard clear all of the data in the Monitor's properties
    #     This should only be called if re-using the same object for a different trace
    #     """
    #     for property in self.symbolic_properties:
    #         property.hard_reset()
    #     self.concrete_properties = []
    #     self.previous_concrete = []
    #     self.violations.clear()

    def check(self, sg, save_usage_information=False):
        if self.ego_id is None:
            for node in sg.nodes:
                if 'ego' == node.name:
                    self.ego_id = node.attr[utils.ID_ATTR]
        # add new concrete properties
        # for symbolic_prop in self.symbolic_properties:
        #     self.concrete_properties.extend(symbolic_prop.make_concrete(sg))
        # additional_concrete = []
        # for concrete_prop in self.concrete_properties:
        #     additional_concrete = concrete_prop.additional_concrete(sg)
        # self.concrete_properties.extend(additional_concrete)
        self.concrete_properties.extend([symbolic_prop.make_blank(sg) for symbolic_prop in self.symbolic_properties])
        to_keep = []
        to_check = self.concrete_properties
        iterations = defaultdict(int)
        while len(to_check) > 0:
        # for concrete_prop in self.concrete_properties:
            concrete_prop = to_check.pop(0)
            iterations[concrete_prop.name] += 1
            concrete_prop.undef = []
            prev_state = concrete_prop.get_current_state()
            try:
                concrete_prop.step(sg)
                if concrete_prop.is_trap():
                    self.previous_concrete.append(concrete_prop)
                    if not concrete_prop.is_accepting():
                        violation = SymbolicViolation(concrete_prop.name,
                                                      sg.graph['frame'],
                                                      concrete_prop.initial_frame,
                                                      concrete_prop.entity_mapping,
                                                      concrete_prop.data_history,
                                                      concrete_prop.name_history,
                                                      concrete_prop.frames,
                                                      self.ego_id)
                        save_dir = self.route_path / concrete_prop.name / 'violations/'
                        save_dir.mkdir(parents=True, exist_ok=True)
                        save_file = save_dir / f'{violation.violation_time}.json'
                        violation.to_json(save_file)
                        self.violations[concrete_prop.name].append(violation)
                else:
                    to_keep.append(concrete_prop)
                # handle undefs that were encountered
                if len(concrete_prop.undef) > 0:
                    concrete_prop.undef = list(set(concrete_prop.undef))  # remove dupes
                    extensions = concrete_prop.additional_concrete_specific(sg, concrete_prop.undef, include_none=False, current_state=prev_state)
                    to_check.extend(extensions)
            except UnboundEntityError as e:
                extensions = concrete_prop.additional_concrete_specific(sg, e.entities, include_none=False, current_state=prev_state)
                to_check.extend(extensions)
        self.concrete_properties = to_keep
        self.iterations_per_frame[sg.graph['frame']] = iterations
        self.timestep += 1

    def save_final_output(self):
        # for symbolic_prop in self.symbolic_properties:
        save_file = self.route_path/'stats.json'
        self.route_path.mkdir(parents=True, exist_ok=True)
        with open(save_file, 'w') as f:
            json.dump(self.iterations_per_frame, f)
        for prop_name, violations in self.violations.items():
            save_dir = self.route_path/prop_name/'violations/'
            save_dir.mkdir(parents=True, exist_ok=True)
            for violation in violations:
                save_file = save_dir/f'{violation.violation_time}.json'
                violation.to_json(save_file)
