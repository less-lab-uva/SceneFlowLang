import SG_Primitives as P
from Property import Property, SubpropertyWrapper
from functools import partial

from SymbolicEntity import SymbolicEntity
from SymbolicProperty import SymbolicProperty

VEHICLE_CLASSES = ['car', 'truck', 'van', 'bus', 'motorcycle', 'bicycle', 'vehicle']
VEHICLE_CLASSES_WITH_EGO = ['ego']
VEHICLE_CLASSES_WITH_EGO.extend(VEHICLE_CLASSES)
MOTOR_VEHICLE_CLASSES = ['car', 'truck', 'van', 'bus', 'motorcycle', 'vehicle']

STOPPED_SPEED = 0.1  # this is a bit fast, but it's what CARLA defines internally
# STOPPED_SPEED = 1e-4


def entity_lanes(entity):
    lanes = partial(P.relSet, entity, "isIn")
    return lanes


def entity_roads(entity):
    roads = partial(P.relSet, entity_lanes(entity), "isIn")
    return roads


def entity_junctions(entity):
    junctions = partial(P.relSet, entity_roads(entity), "isIn")
    return junctions


def stop_signs_for(entity):
    entity_lanes = partial(P.relSet, entity, "isIn")
    entity_roads = partial(P.relSet, entity_lanes, "isIn")
    entity_junctions = partial(P.relSet, entity_roads, "isIn")
    entities_in_junction_with = partial(P.relSet, partial(P.relSet, partial(P.relSet, entity_junctions, "isIn",
                                                                                edge_type='incoming'), "isIn",
                                                              edge_type='incoming'), "isIn", edge_type='incoming')
    entity_if_in_junction = partial(P.intersection, entities_in_junction_with, entity)
    entity_if_not_in_junction = partial(P.symmetric_difference, entity_if_in_junction, entity)
    potential_stop_signs_naive = partial(P.intersection,
                                                 partial(P.relSet, partial(P.relSet, entity_if_not_in_junction, "isIn"),
                                                         "controlsTrafficOf", edge_type="incoming"),
                                                 partial(P.filterByAttr, "G", "name", "stop_sign*"))
    potential_stop_signs = partial(P.union,
                                           potential_stop_signs_naive,
                                           partial(P.intersection,
                                                   partial(P.relSet,
                                                           partial(P.intersection,
                                                                   partial(P.relSet,
                                                                           partial(P.relSet, entity_if_not_in_junction,
                                                                                   "isIn"), "toLeftOf"),
                                                                   partial(P.relSet,
                                                                           partial(P.relSet, entity_if_not_in_junction,
                                                                                   "isIn"), "laneChange")
                                                                   ), "controlsTrafficOf", edge_type="incoming"),
                                                   partial(P.filterByAttr, "G", "name", "stop_sign*"))
                                           )
    entity_opp_lanes = partial(P.relSet, entity_lanes, "opposes")
    stop_signs_for_opp_lanes = partial(P.intersection,
                                           partial(P.relSet, entity_opp_lanes, "controlsTrafficOf",
                                                   edge_type="incoming"),
                                           partial(P.filterByAttr, "G", "name", "stop_sign*"))
    stop_signs = partial(P.difference, potential_stop_signs, stop_signs_for_opp_lanes)
    return stop_signs


def has_stop_signs(entity):
    return partial(P.gt, partial(P.size, stop_signs_for(entity)), 0)


def set_size_eq(nodes, size):
    return partial(P.eq, partial(P.size, nodes), size)

def sym_entities_not_equal(entity1, entity2):
    # two symbolic entities are not equal if they each are sets of size 1 and the set1 - set2 is size 1
    return partial(P.logic_and,
                   partial(P.logic_and,set_size_eq(entity1, 1), set_size_eq(entity2, 1)),
                         set_size_eq(partial(P.difference, entity1, entity2), 1)
                   )

def non_empty(nodes):
    return partial(P.gt, partial(P.size, nodes), 0)


# EGO = partial(P.filterByAttr, "G", "name", "ego")
# EGO_LANES = partial(P.relSet, "Ego", "isIn")
# EGO_ROADS = partial(P.relSet, EGO_LANES, "isIn")
# EGO_JUNCTIONS = partial(P.relSet, EGO_ROADS, "isIn")
#
# # INT_VEHICLE_YIELD = SymbolicEntity('yield_vehicle', ['car', 'truck', 'van'])
# INT_VEHICLE_YIELD = SymbolicEntity('yield_vehicle', ['van'])
# INT_VEHICLE_LANES = partial(P.relSet, INT_VEHICLE_YIELD, "isIn")
# INT_VEHICLE_ROADS = partial(P.relSet, INT_VEHICLE_LANES, "isIn")
# INT_VEHICLE_JUNCTIONS = partial(P.relSet, INT_VEHICLE_ROADS, "isIn")


# INT_VEHICLE_EGO_JUNCTIONS = partial(P.intersection, INT_VEHICLE_JUNCTIONS, EGO_JUNCTIONS)
# EGO_LEFT_OF = partial(P.relSet, EGO, "toLeftOf", edge_type="incoming")

YIELD_JUNCTION = SymbolicEntity('yield_junction', base_filter=['junction'])
YIELD_JUNCTION_ROADS = partial(P.relSet, YIELD_JUNCTION, "isIn", edge_type="incoming")

# INT_VEHICLE_AT_JUNCTION = partial(P.eq,
#                                   partial(P.size, partial(P.intersection, INT_VEHICLE_JUNCTIONS, YIELD_JUNCTION)),
#                                   1)
# INT_VEHICLE_ONLY_IN_JUNCTION = partial(P.eq, partial(P.size, partial(P.difference, INT_VEHICLE_ROADS, YIELD_JUNCTION_ROADS)), 0)
#
# EGO_AT_JUNCTION = partial(P.eq, partial(P.size, partial(P.intersection, EGO_JUNCTIONS, YIELD_JUNCTION)), 1)
# EGO_ONLY_IN_JUNCTION = partial(P.eq, partial(P.size, partial(P.difference, EGO_ROADS, YIELD_JUNCTION_ROADS)), 0)
# EGO_IS_LEFT_OF_INT_VEHICLE = partial(P.eq, partial(P.size, partial(P.intersection, EGO_LEFT_OF, INT_VEHICLE_YIELD)), 1)
#
# intersection_left_yield = SymbolicProperty(
#     "intersection_left_yield",
#     "(((!(ego) & !(a)) & X((ego & a & isleft))) -> X(X((ego U !(a)))))",
#     [("ego", EGO_AT_JUNCTION),
#      ("a", INT_VEHICLE_AT_JUNCTION),
#      ("isleft", EGO_IS_LEFT_OF_INT_VEHICLE)],
#     [INT_VEHICLE_YIELD, YIELD_JUNCTION])
#
# ego_intersection_yield = SymbolicProperty(
#     "ego_intersection_yield",
#     "(((!(ego) & (a)) & X((ego & a))) -> X(X((ego U !(a)))))",
#     [("ego", EGO_AT_JUNCTION),
#      ("a", INT_VEHICLE_AT_JUNCTION)],
#     [INT_VEHICLE_YIELD, YIELD_JUNCTION])
#
# # intersection_yield_to_ego = SymbolicProperty(
# #     "intersection_yield_to_ego",
# #     "((((ego) & !(a)) & X((ego & a))) -> X(X((a U !(ego)))))",
# #     [("ego", EGO_AT_JUNCTION),
# #      ("a", INT_VEHICLE_AT_JUNCTION)],
# #     [INT_VEHICLE_YIELD, YIELD_JUNCTION])
#
# # TODO actually check for stop signs
# intersection_yield_to_ego = SymbolicProperty(
#     "intersection_yield_to_ego",
#     "((((ego_at_junc) & !(other_at_junc)) & X((ego_at_junc & other_at_junc))) -> X(X(((other_at_junc & !other_only_in_junc) U !(ego_at_junc)))))",
#     [("ego_at_junc", EGO_AT_JUNCTION),
#      ("other_at_junc", INT_VEHICLE_AT_JUNCTION),
#      ("other_only_in_junc", INT_VEHICLE_ONLY_IN_JUNCTION)],
#     [INT_VEHICLE_YIELD, YIELD_JUNCTION])

YIELD_VEHICLE1 = SymbolicEntity('yield_vehicle_1', VEHICLE_CLASSES_WITH_EGO)
YIELD_VEHICLE2 = SymbolicEntity('yield_vehicle_2', VEHICLE_CLASSES_WITH_EGO)

def is_in_junction(vehicle, junction):
    return partial(P.eq,partial(P.size, partial(P.intersection, entity_junctions(vehicle), junction)), 1)

YIELD_VEHICLE2_ONLY_IN_JUNCTION = partial(P.eq, partial(P.size, partial(P.difference, entity_roads(YIELD_VEHICLE2), YIELD_JUNCTION_ROADS)), 0)

symbolic_stop_sign_yield = SymbolicProperty(
    "821_vehicle2_needs_to_yield_to_vehicle1_stop",
    "((((v1_at_junc) & !(v2_at_junc) & v2_has_stop) & X((v1_at_junc & v2_at_junc))) -> X(X(((v2_at_junc & !v2_only_in_junc) U !(v1_at_junc)))))",
    [("v1_at_junc", is_in_junction(YIELD_VEHICLE1, YIELD_JUNCTION)),
     ("v2_at_junc", is_in_junction(YIELD_VEHICLE2, YIELD_JUNCTION)),
     ("v2_only_in_junc", YIELD_VEHICLE2_ONLY_IN_JUNCTION),
     ("v2_has_stop", has_stop_signs(YIELD_VEHICLE2))],
    [YIELD_VEHICLE1, YIELD_VEHICLE2, YIELD_JUNCTION])

symbolic_stop_sign_tie_left_yield = SymbolicProperty(
    "820_vehicle2_needs_to_yield_to_vehicle1_stop_tie",
    "((((!v1_at_junc) & !(v2_at_junc) & v2_has_stop & v1_has_stop) & X((v1_at_junc & v2_at_junc & v2_right_of_v1))) -> X(X(((v2_at_junc & !v2_only_in_junc) U !(v1_at_junc)))))",
    [("v1_at_junc", is_in_junction(YIELD_VEHICLE1, YIELD_JUNCTION)),
     ("v2_at_junc", is_in_junction(YIELD_VEHICLE2, YIELD_JUNCTION)),
     ("v2_only_in_junc", YIELD_VEHICLE2_ONLY_IN_JUNCTION),
     ("v1_has_stop", has_stop_signs(YIELD_VEHICLE1)),
     ("v2_has_stop", has_stop_signs(YIELD_VEHICLE2)),
     ("v2_right_of_v1", partial(P.eq,
                                partial(P.size,
                                        partial(P.intersection,
                                                partial(P.relSet, YIELD_VEHICLE2, "toRightOf"),
                                                YIELD_VEHICLE1)),
                                1))
     ],
    [YIELD_VEHICLE1, YIELD_VEHICLE2, YIELD_JUNCTION])


def is_emergency_vehicle(vehicle):
    return partial(P.eq,
            partial(P.size,
                    partial(P.intersection,
                            vehicle,
                            partial(P.filterByAttr, vehicle, "carla_type_id", lambda x: x is not None and 'ambulance' in x)
                            )
                    ),
            1)


def has_lights_on(vehicle, light_type):
    return partial(P.eq,
            partial(P.size,
                    partial(P.intersection,
                            vehicle,
                            partial(P.filterByAttr, vehicle, light_type, lambda x: x)
                            )
                    ),
            1)


def has_emergency_lights_on(vehicle):
    return partial(P.logic_or, has_lights_on(vehicle, 'light_Special1'), has_lights_on(vehicle, 'light_Special2'))


symbolic_stop_sign_yield_to_emergency = SymbolicProperty(
    "829_vehicle2_needs_to_yield_to_emergency",
    "(((!(v2_at_junc)) & X((emergency_at_junc & emergency_has_lights & v2_at_junc & v1_not_v2))) -> X(X(((v2_at_junc & !v2_only_in_junc) U !(emergency_at_junc)))))",
    [("emergency_at_junc", partial(P.logic_and,
                                   is_in_junction(YIELD_VEHICLE1, YIELD_JUNCTION),
                                          is_emergency_vehicle(YIELD_VEHICLE1))
      ),
     ('emergency_has_lights', has_emergency_lights_on(YIELD_VEHICLE1)),
     ("v2_at_junc", is_in_junction(YIELD_VEHICLE2, YIELD_JUNCTION)),
     ("v2_only_in_junc", YIELD_VEHICLE2_ONLY_IN_JUNCTION),
     ("v2_has_stop", has_stop_signs(YIELD_VEHICLE2)),
      ("v1_not_v2", sym_entities_not_equal(YIELD_VEHICLE1, YIELD_VEHICLE2))],
    [YIELD_VEHICLE1, YIELD_VEHICLE2, YIELD_JUNCTION])


def is_too_close(vehicle2, vehicle1, distance):
    """Return a partial that calculates if vehicle2 is too close to vehicle 1"""
    close_to_vehicle_2 = entities_within(vehicle2, distance)
    # if the intersection of the things "close to" vehicle2 with vehicle 1 is size 1, then vehicle 2 was near vehicle 1
    return set_size_eq(partial(P.intersection, close_to_vehicle_2, vehicle1), 1)

def is_too_close_bike(vehicle2, vehicle1, add_buffer=False):
    """Return a partial that calculates if vehicle2 is too close to vehicle 1"""
    close_to_vehicle_2 = partial(P.relSet, vehicle2, "safe_hazard")
    if add_buffer:
        close_to_vehicle_2 = partial(P.union, close_to_vehicle_2, partial(P.relSet, vehicle2, "near_coll"))
    # if the intersection of the things "close to" vehicle2 with vehicle 1 is size 1, then vehicle 2 was near vehicle 1
    return set_size_eq(partial(P.intersection, close_to_vehicle_2, vehicle1), 1)


def is_too_close_emergency(vehicle2, vehicle1):
    """Return a partial that calculates if vehicle2 is too close to vehicle 1"""
    close_to_vehicle_2 = partial(P.union, partial(P.relSet, vehicle2, "safe_hazard"),
                                 partial(P.relSet, vehicle2, "near_coll"))
    close_to_vehicle_2 = partial(P.union, close_to_vehicle_2,
                                 partial(P.relSet, vehicle2, "super_near"))
    close_to_vehicle_2 = partial(P.union, close_to_vehicle_2,
                                 partial(P.relSet, vehicle2, "very_near"))
    close_to_vehicle_2 = partial(P.union, close_to_vehicle_2,
                                 partial(P.relSet, vehicle2, "near"))
    close_to_vehicle_2 = partial(P.union, close_to_vehicle_2,
                                 partial(P.relSet, vehicle2, "visible"))
    # if the intersection of the things "close to" vehicle2 with vehicle 1 is size 1, then vehicle 2 was near vehicle 1
    return set_size_eq(partial(P.intersection, close_to_vehicle_2, vehicle1), 1)


def same_lane(vehicle1, vehicle2):
    return non_empty(partial(P.intersection, entity_lanes(vehicle1), entity_lanes(vehicle2)))

def behind(vehicle1, vehicle2):
    """Return a partial that calcs if vehicle2 is behind vehicle 1"""
    behind_v1_entities = partial(P.union, partial(P.relSet, vehicle1, "atDRearOf"),
                                 partial(P.relSet, vehicle1, "atSRearOf"))
    is_behind_v1 = set_size_eq(partial(P.intersection, behind_v1_entities, vehicle2), 1)
    front_v2_entities = partial(P.union, partial(P.relSet, vehicle2, "inDFrontOf"),
                                 partial(P.relSet, vehicle2, "inSFrontOf"))
    is_front_v2 = set_size_eq(partial(P.intersection, front_v2_entities, vehicle1), 1)
    return partial(P.logic_and, is_behind_v1, is_front_v2)



def is_moving(entity):
    """Returns a partial evaluating if entity is moving"""
    return partial(P.eq, partial(P.size,
                          partial(P.filterByAttr, entity, "carla_speed",
                                  (lambda a: a is not None and P.gt(a, STOPPED_SPEED)))), 1)


def no_following(follow_duration, follow_distance):
    no_following = SymbolicProperty(
        f"816_vehicle2_cannot_follow_vehicle1_{follow_duration}_{follow_distance}",
        f"(~(too_close & same_lane & behind & is_moving) & X(too_close & same_lane & behind & is_moving)) -> X(~ $[{follow_duration}][too_close & same_lane & behind & is_moving])",
        [("too_close", is_too_close(YIELD_VEHICLE2, YIELD_VEHICLE1, follow_distance)),
                    ("same_lane", same_lane(YIELD_VEHICLE2, YIELD_VEHICLE1)),
                    ("behind", behind(YIELD_VEHICLE2, YIELD_VEHICLE1)),
                    ("is_moving", is_moving(YIELD_VEHICLE2)),],
    [YIELD_VEHICLE1, YIELD_VEHICLE2])
    return no_following


def no_following_emergency(follow_duration):
    no_following_emergency = SymbolicProperty(
        f"921_vehicle2_cannot_follow_emergency_vehicle1_{follow_duration}",
        f"(~(too_close & same_lane & behind & v1_emergency) & X(too_close & same_lane & behind & v1_emergency)) -> X(~ $[{follow_duration}][too_close & same_lane & behind & v1_emergency])",
        [("too_close", is_too_close_emergency(YIELD_VEHICLE2, YIELD_VEHICLE1)),
                    ("same_lane", same_lane(YIELD_VEHICLE2, YIELD_VEHICLE1)),
                    ("behind", behind(YIELD_VEHICLE2, YIELD_VEHICLE1)),
                    ("v1_emergency", is_emergency_vehicle(YIELD_VEHICLE1)),],
    [YIELD_VEHICLE1, YIELD_VEHICLE2])
    return no_following_emergency


LANE_VEHICLE1 = SymbolicEntity('lane_vehicle_1', VEHICLE_CLASSES_WITH_EGO)
LANE1 = SymbolicEntity('lane_1', ['lane'])
LANE2 = SymbolicEntity('lane_2', ['lane'])


def only_in_lane(vehicle, lane):
    """True iff the vehicle is in the lane and no other lanes"""
    return partial(P.logic_and, partial(P.eq, partial(P.size, partial(P.symmetric_difference, entity_lanes(vehicle), lane)), 0),
                   partial(P.defined, lane))

def in_lane(vehicle, lane):
    """True iff the vehicle is in the lane"""
    return non_empty(partial(P.intersection, lane, entity_lanes(vehicle)))


def lane_in_junction(lane):
    return partial(P.gt, partial(P.size, partial(P.relSet, partial(P.relSet, lane, "isIn"), "isIn")), 0)


def is_in_a_junction(vehicle):
    return partial(P.gt, partial(P.size, entity_junctions(vehicle)), 0)


def only_in_junction(vehicle):
    not_out_of_junction = partial(P.eq, partial(P.size, partial(P.difference, entity_roads(vehicle), partial(P.relSet, entity_junctions(vehicle), "isIn", edge_type="incoming"))), 0)
    return partial(P.logic_and, is_in_a_junction(vehicle), not_out_of_junction)


def lanes_to_right(lane):
    return partial(P.relSet, lane, 'toRightOf', edge_type="incoming")

def rightmost(lane):
    return partial(P.eq, partial(P.size, lanes_to_right(lane)), 0)


def lanes_to_left(lane):
    return partial(P.difference,
                        partial(P.relSet, lane, 'toLeftOf', edge_type="incoming"),
                        partial(P.relSet, lane, 'opposes', edge_type="incoming"))

def leftmost(lane):
    # lanes to the left \ opposing lanes
    return partial(P.eq, partial(P.size, lanes_to_left(lane)), 0)

def lanes_match(lane1, lane2):
    # if right:
    l1_rightmost = rightmost(lane1)
    l2_rightmost = rightmost(lane2)
    rightmost_equal = partial(P.boolean_equals, l1_rightmost, l2_rightmost)
        # return rightmost_equal
    # else:
        # lanes to the left \ opposing lanes
    l1_leftmost = leftmost(lane1)
    l2_leftmost = leftmost(lane2)
    leftmost_equal = partial(P.boolean_equals, l1_leftmost, l2_leftmost)
        # return leftmost_equal
    return partial(P.logic_and, rightmost_equal, leftmost_equal)


def two_lane_road(lane):
    lane_to_left = lanes_to_left(lane)
    two_to_left = lanes_to_left(lane_to_left)

    lane_to_right = lanes_to_right(lane)
    two_to_right = lanes_to_right(lane_to_right)

    two_lane_right = partial(P.logic_and,
                             partial(P.logic_and,
                                     set_size_eq(lane_to_right, 0),
                                     set_size_eq(lane_to_left, 1)),
                             set_size_eq(two_to_left, 0)
                             )
    two_lane_left = partial(P.logic_and,
                             partial(P.logic_and,
                                     set_size_eq(lane_to_left, 0),
                                     set_size_eq(lane_to_right, 1)),
                             set_size_eq(two_to_right, 0)
                             )
    return partial(P.logic_or, two_lane_right, two_lane_left)



only_in_lane2 = partial(P.ite,
                        partial(P.defined, LANE2),
                        # partial(P.logic_implies, two_lane_road(LANE2),
                        # partial(P.logic_and,
                        #         partial(P.logic_not, lane_in_junction(LANE2)),
                        #                 only_in_lane(LANE_VEHICLE1, LANE2)))
                partial(P.logic_and,
                        partial(P.logic_and, two_lane_road(LANE2), partial(P.logic_not, lane_in_junction(LANE2))),
                        only_in_lane(LANE_VEHICLE1, LANE2))
                        , False)


def lane_arity_matches():
    lane_matches = SymbolicProperty(f"846_lane_you_leave_must_match_lane_you_enter",
        # "((only_in_lane1 & X(only_in_junction) & X(X(((only_in_junction & !(only_in_lane2)) U (only_in_lane2 | !(only_in_junction)))))) -> (only_in_lane1 & X(only_in_junction) & X(X(((only_in_junction & !(only_in_lane2)) U (only_in_lane2 & lane1_match_lane2))))))",
                                  "((only_in_lane1 & X(only_in_junction) & X(X(((only_in_junction & !(only_in_lane2)) U only_in_lane2)))) -> (only_in_lane1 & X(only_in_junction) & X(X(((only_in_junction & !(only_in_lane2)) U (only_in_lane2 & lane1_match_lane2))))))",
        [("only_in_lane1",
        partial(P.logic_and,
          partial(
             P.logic_and, (partial(P.logic_not, lane_in_junction(LANE1))),
                           only_in_lane(LANE_VEHICLE1, LANE1)
         ),
                two_lane_road(LANE1))),
         ("only_in_junction", is_in_a_junction(LANE_VEHICLE1)),
         ("only_in_lane2", only_in_lane2),
         ("lane1_match_lane2", lanes_match(LANE1, LANE2))],
        [LANE_VEHICLE1, LANE1, LANE2])
    return lane_matches


PASS_VEHICLE1 = SymbolicEntity('pass_vehicle_1', VEHICLE_CLASSES_WITH_EGO)
BIKE1 = SymbolicEntity('bike_1', ['bicycle'])

def is_direct_right_of(vehicle1, vehicle2):
    """Returns if vehicle 2 is to the direct right of vehicle 1"""
    # right_v1_entities = partial(P.relSet, vehicle1, "toRightOf", edge_type='incoming')
    # check from our perspective instead
    right_v1_entities = partial(P.relSet, vehicle2, "toRightOf")
    side_v1_entities = partial(P.union, partial(P.relSet, vehicle2, "atSRearOf"),
                                 partial(P.relSet, vehicle2, "inSFrontOf"))
    side_right_v1_entities = partial(P.intersection, right_v1_entities, side_v1_entities)
    return set_size_eq(partial(P.intersection, side_right_v1_entities, vehicle1), 1)

def give_bikes_room(buffer=False):
    give_bikes_room_passing = SymbolicProperty(f"839_give_bikes_room_passing{'_buffer' if buffer else ''}",
       # ((q & !(r) & F((r | !(p)))) -> X((p U r)))
        "((behind_bike & bike_safe_distance & !(in_front_bike) & F((in_front_bike | !(bike_safe_distance)))) -> X((bike_safe_distance U in_front_bike)))",
    # "((behind_bike & !(in_front_bike) & F((in_front_bike | !(bike_safe_distance)))) -> (bike_safe_distance U in_front_bike))",
        [
                   ("behind_bike", partial(P.logic_and, behind(PASS_VEHICLE1, BIKE1), same_lane(BIKE1, PASS_VEHICLE1))),
                   # ("in_front_bike", partial(P.logic_and, behind(BIKE1, PASS_VEHICLE1), same_lane(BIKE1, PASS_VEHICLE1))),
                   ("in_front_bike", partial(P.logic_implies,
                                             same_lane(BIKE1, PASS_VEHICLE1),
                                             behind(BIKE1, PASS_VEHICLE1))),
                   ("bike_safe_distance",
                    partial(P.logic_and,
                            partial(P.logic_not, is_too_close_bike(PASS_VEHICLE1, BIKE1, add_buffer=buffer)),
                            partial(P.logic_not, is_direct_right_of(BIKE1, PASS_VEHICLE1))
                            )
                   )
                   ],
        [PASS_VEHICLE1, BIKE1])
    return give_bikes_room_passing

# give_bikes_room_passing_buffer = SymbolicProperty("839_give_bikes_room_passing_buffer",
#    # ((q & !(r) & F((r | !(p)))) -> X((p U r)))
#     "((behind_bike & bike_safe_distance & !(in_front_bike) & F((in_front_bike | !(bike_safe_distance)))) -> X((bike_safe_distance U in_front_bike)))",
#    #    "((behind_bike & !(in_front_bike) & F((in_front_bike | !(bike_safe_distance)))) -> (bike_safe_distance U in_front_bike))",
#     [
#                ("behind_bike", partial(P.logic_and, behind(PASS_VEHICLE1, BIKE1), same_lane(BIKE1, PASS_VEHICLE1))),
#                ("in_front_bike", partial(P.logic_and, behind(BIKE1, PASS_VEHICLE1), same_lane(BIKE1, PASS_VEHICLE1))),
#                ("bike_safe_distance",
#                 partial(P.logic_and,
#                         partial(P.logic_not, is_too_close_bike(PASS_VEHICLE1, BIKE1, add_buffer=True)),
#                         partial(P.logic_not, is_direct_right_of(BIKE1, PASS_VEHICLE1))
#                         )
#                )
#                ],
#     [PASS_VEHICLE1, BIKE1])

ENTITY_BEING_PASSED = SymbolicEntity('entity_being_passed', VEHICLE_CLASSES_WITH_EGO)


def entities_within(entity, distance):
    if distance == 'safe_hazard':
        return partial(P.relSet, entity, "safe_hazard")
    close_to_entity = partial(P.union, partial(P.relSet, entity, "safe_hazard"),
                                 partial(P.relSet, entity, "near_coll"))
    if distance == 'near_coll':
        return close_to_entity
    close_to_entity = partial(P.union, close_to_entity,
                                 partial(P.relSet, entity, "super_near"))
    if distance == 'super_near':
        return close_to_entity
    close_to_entity = partial(P.union, close_to_entity,
                                 partial(P.relSet, entity, "very_near"))
    if distance == 'very_near':
        return close_to_entity
    close_to_entity = partial(P.union, close_to_entity,
                                 partial(P.relSet, entity, "near"))
    if distance == 'near':
        return close_to_entity
    close_to_entity = partial(P.union, close_to_entity,
                                 partial(P.relSet, entity, "visible"))
    return close_to_entity

def opposing_lane_clear(entity, lane):
    opposing_lane = partial(P.relSet, lane, "opposes")
    opposing_lane_entities = partial(P.relSet, opposing_lane, "isIn", edge_type="incoming")
    entities_to_avoid = partial(P.intersection,
                                entities_within(entity, distance='visible'),
                                opposing_lane_entities)
    # clear if set is empty
    lane_clear = set_size_eq(entities_to_avoid, 0)
    # if we are in the opp lane, it better be clear
    return partial(P.logic_implies, in_lane(entity, opposing_lane), lane_clear)


def observed_entity(entity):
    return set_size_eq(partial(P.filterByAttr, entity, "PHANTOM", lambda x: x), 0)


opp_clear_for_crossing = SymbolicProperty("843_opp_clear_for_crossing",
   # ((q & !(r) & F((r | !(p)))) -> X((p U r)))
    "((behind_entity & opp_clear & !(in_front_entity) & in_one_lane & F(((in_front_entity & in_one_lane) | !(opp_clear)))) -> X((opp_clear U (in_front_entity & in_one_lane))))",
    [
               ("behind_entity", partial(P.logic_and, behind(PASS_VEHICLE1, ENTITY_BEING_PASSED), same_lane(ENTITY_BEING_PASSED, PASS_VEHICLE1))),
               ("in_front_entity", partial(P.logic_implies, observed_entity(ENTITY_BEING_PASSED), partial(P.logic_and, behind(ENTITY_BEING_PASSED, PASS_VEHICLE1), same_lane(ENTITY_BEING_PASSED, PASS_VEHICLE1)))),
               ("opp_clear", opposing_lane_clear(PASS_VEHICLE1, LANE1)),
              ("in_one_lane", partial(
                  P.logic_and, (partial(P.logic_not, lane_in_junction(LANE1))),
                  only_in_lane(PASS_VEHICLE1, LANE1)
              )),
               ],
    [PASS_VEHICLE1, ENTITY_BEING_PASSED, LANE1])

# lane_arity_doesnt_matches = SymbolicProperty("lane_you_leave_must_not_match_lane_you_enter",
#     # "((only_in_lane1 & X(only_in_junction) & X(X(((only_in_junction & !(only_in_lane2)) U (only_in_lane2 | !(only_in_junction)))))) -> (only_in_lane1 & X(only_in_junction) & X(X(((only_in_junction & !(only_in_lane2)) U (only_in_lane2 & lane1_match_lane2))))))",
# "((only_in_lane1 & X(only_in_junction) & X(X(((only_in_junction & !(only_in_lane2)) U only_in_lane2)))) -> (only_in_lane1 & X(only_in_junction) & X(X(((only_in_junction & !(only_in_lane2)) U (only_in_lane2 & lane1_match_lane2))))))",
#      [("only_in_lane1", partial(
#          P.logic_and, (partial(P.logic_not, lane_in_junction(LANE1))),
#                        only_in_lane(LANE_VEHICLE1, LANE1)
#      )),
#      ("only_in_junction", is_in_a_junction(LANE_VEHICLE1)),
#      ("only_in_lane2", only_in_lane2),
#      ("lane1_match_lane2", partial(P.logic_not, lanes_match(LANE1, LANE2)))
#       ],
#     [LANE_VEHICLE1, LANE1, LANE2])


all_symbolic_properties = [symbolic_stop_sign_yield, symbolic_stop_sign_tie_left_yield,
                           symbolic_stop_sign_yield_to_emergency,
                           # lane_arity_matches(False), lane_arity_matches(True),
                           lane_arity_matches(),
                           give_bikes_room(False), give_bikes_room(True),
                           opp_clear_for_crossing, no_following_emergency(10)]
#
#
# for follow_duration in [10, 50]:
#     all_symbolic_properties.append(no_following(follow_duration))
#     all_symbolic_properties.append(no_following_emergency(follow_duration))

# all_symbolic_properties = []
for frames in [10, 50]:
    for distances in ['visible', 'super_near']:
        all_symbolic_properties.append(no_following(frames, distances))
# all_symbolic_properties = [no_following(10, "visible"), no_following(10, "super_near")]
# all_symbolic_properties.extend([lane_arity_matches, lane_arity_doesnt_matches])
# # all_symbolic_properties = [intersection_yield_to_ego]