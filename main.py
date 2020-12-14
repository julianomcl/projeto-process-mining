import itertools
from time import process_time as pt
from datetime import datetime
import snakes.plugins
from snakes.nets import PetriNet, Place, Transition, Value
from sortedcontainers import SortedSet, SortedDict

snakes.plugins.load('gv', 'snakes.nets', 'nets')
from nets import *

RIGHT_CAUSALITY = '->'
LEFT_CAUSALITY = '<-'
PARALLEL = '||'
CHOICES = '#'


def read_log_file(log_file_path):
    with open(log_file_path, 'r') as log_file:
        log_traces = SortedDict()
        content = log_file.read()
        lines = content.split('\n')
        for line in lines[1:]:
            if line != '':
                case_id, activity, *event_data = line.split(',')
                if case_id not in log_traces:
                    log_traces[case_id] = []

                log_traces[case_id].append(activity)

        return log_traces


def check_set(set_a, pairs):
    for activity1 in set_a:
        for activity2 in set_a:
            if (activity1, activity2) not in pairs:
                return False
    return True


def check_outsets(set_a, set_b, pairs):
    for activity1 in set_a:
        for activity2 in set_b:
            if (activity1, activity2) not in pairs:
                return False
    return True


# Step 1
def get_activities(traces):
    # percorre todas as atividades do log, gerando um conjunto ordenado de todas as atividades
    activities = SortedSet((activity for trace in traces.values() for activity in trace))
    print('Tl = {', ', '.join(activities), '}')
    return activities


# Step 2
def get_start_activities(traces):
    # percorre todas as primeiras atividades dos traces, gerando um conjunto ordenado atividades de início
    start_activities = SortedSet(trace[0] for trace in traces.values())
    print('Ti = {', ', '.join(start_activities), '}')

    return start_activities


# Step 3
def get_end_activities(traces):
    # percorre todas as últimas atividades dos traces, gerando um conjunto ordenado das atividades de fim
    end_activities = SortedSet(trace[-1] for trace in traces.values())
    print('To = {', ', '.join(end_activities), '}')

    return end_activities


# Step 4-1
def get_footprint(traces, activities):
    footprint = SortedDict()
    unique_traces = SortedSet()
    for trace in traces.values():
        unique_traces.add('|' + '| > |'.join(trace) + '|')

    for activity1 in activities:
        footprint[activity1] = SortedDict()
        for activity2 in activities:
            relation = CHOICES
            directly_follows = '|' + activity1 + '| > |' + activity2 + '|'
            for trace in unique_traces:
                if trace.find(directly_follows) >= 0:
                    if relation == LEFT_CAUSALITY:
                        relation = PARALLEL
                    else:
                        relation = RIGHT_CAUSALITY

                inverse_directly_follows = '|' + activity2 + '| > |' + activity1 + '|'
                if trace.find(inverse_directly_follows) >= 0:
                    if relation == RIGHT_CAUSALITY:
                        relation = PARALLEL
                    else:
                        relation = LEFT_CAUSALITY
            footprint[activity1][activity2] = relation

    return footprint


# Step 4-2
def get_pairs(footprint):
    pairs_causality = set()
    pairs_not_causality = set()
    for activity1, relations in footprint.items():
        for activity2, relation in relations.items():
            if relation == RIGHT_CAUSALITY:
                pairs_causality.add((activity1, activity2))
            if relation == CHOICES:
                pairs_not_causality.add((activity1, activity2))

    pairs = set()
    subsets = set()
    activities = tuple((activity for activity in footprint.keys()))

    range_n = min(4, len(activities))
    for i in range(1, range_n):
        for combination in itertools.combinations(activities, i):
            subsets.add(combination)
    for set_a in subsets:
        check_a = check_set(set_a, pairs_not_causality)
        for set_b in subsets:
            check_b = check_set(set_b, pairs_not_causality)
            if check_a and check_b and check_outsets(set_a, set_b, pairs_causality):
                pairs.add((set_a, set_b))

    print('Xl =', pairs)
    return pairs


# Step 5
def get_maximal_pairs(pairs):
    i = 0
    pair_appended = []
    maximal_pairs = []
    for pair_a in pairs:
        append = True
        flat_pair_a = []
        for pair_sets in pair_a:
            for pair_element in pair_sets:
                flat_pair_a.append(pair_element)
        j = 0
        for pair_b in pairs:
            if i != j:
                flat_pair_b = []
                for pair_sets in pair_b:
                    for pair_element in pair_sets:
                        flat_pair_b.append(pair_element)

                if SortedSet(flat_pair_a).issubset(flat_pair_b) and SortedSet(flat_pair_a) != SortedSet(flat_pair_b):
                    append = False
            j = j + 1

        if append:
            if SortedSet(flat_pair_a) not in pair_appended:
                maximal_pairs.append(pair_a)
                pair_appended.append(SortedSet(flat_pair_a))
        i = i + 1

    print('Yl = {', maximal_pairs, '}')
    return maximal_pairs


# Step 6
def get_places(start_activities, end_activities, maximal_pairs):
    places = [('Pi', start_activities)]
    place_n = 1
    for pair in maximal_pairs:
        places.append((pair[0], 'P' + str(place_n), pair[1]))
        place_n += 1
    places.append((end_activities, 'Po'))

    print('Pl = {', places, '}')
    return places


# Step 7 and 8
def get_petrinet(activities, places):
    petrinet = PetriNet('N')
    place_n = 0
    first_place = places[0]
    last_place = places[-1]

    petrinet.add_place(Place(first_place[0]))
    petrinet.add_place(Place(last_place[1]))
    for place in places[1:-1]:
        place_name = place[1]
        petrinet.add_place(Place(place_name))
        place_n += 1

    for transition in activities:
        petrinet.add_transition(Transition(transition))

    for transition in first_place[1]:
        petrinet.add_input(first_place[0], transition, Value(''))

    place_n = 1
    for place in places[1:-1]:
        output_transitions = (isinstance(place[0], str) and [place[0]] or place[0])
        input_transitions = (isinstance(place[2], str) and [place[2]] or place[2])
        for transition in output_transitions:
            petrinet.add_output(place[1], transition, Value(''))

        for transition in input_transitions:
            petrinet.add_input(place[1], transition, Value(''))
        place_n += 1

    for transition in last_place[0]:
        petrinet.add_output(last_place[1], transition, Value(''))

    return petrinet


def generate_petrinet_png(petrinet, file_name='petrinet.png'):
    def draw_place(place, attr):
        if attr['label'].find('Pi') >= 0:
            attr['color'] = '#FF0000'
            attr['width'] = 0.6
        if attr['label'].find('Po') >= 0:
            attr['color'] = '#00FF00'
            attr['width'] = 0.6
        attr['shape'] = 'circle'
        attr['label'] = ''

    def draw_transition(transition, attr):
        attr['label'] = transition.name

    def draw_arc(arc, attr):
        attr['label'] = ''

    petrinet.draw(file_name, place_attr=draw_place, trans_attr=draw_transition, arc_attr=draw_arc)
    print(f'Generated PetriNet in file: {file_name}')

    petrinet.draw(file_name + '.dot', place_attr=draw_place, trans_attr=draw_transition, arc_attr=draw_arc)
    print(f'Generated PetriNet dot in file: {file_name}.dot')
    print()


def execute_alpha_miner(traces, file_name='petrinet.png'):
    activities = get_activities(traces)
    start_activities = get_start_activities(traces)
    end_activities = get_end_activities(traces)
    footprint = get_footprint(traces, activities)
    pairs = get_pairs(footprint)
    maximal_pairs = get_maximal_pairs(pairs)
    places = get_places(start_activities, end_activities, maximal_pairs)
    petrinet = get_petrinet(activities, places)
    generate_petrinet_png(petrinet, file_name)

    return activities


def process_log(start_time, process_time, log_traces, activities):
    # geração de arquivo com algumas variáveis uteis à análise da execução
    process_end = pt() - process_time
    log_size = len(log_traces)
    activities_size = len(activities)

    log_messages = [f'Execution start: \t{start_time}',
                    f'Total instances: \t{log_size} cases',
                    f'Total activities:\t{activities_size}',
                    f'Process Time:    \t{process_end:.3f}ms']

    with open('process_log.txt', 'a') as file:
        for message in log_messages:
            print(message)
            file.write(f'{message}\n')

    file.close()


if __name__ == '__main__':
    start_time = datetime.now()
    process_time = pt()
    log_traces = read_log_file('simulation_logs_simplified.csv')
    # log_traces = read_log_file('aalst_log.csv')
    activities = execute_alpha_miner(log_traces)
    process_log(start_time, process_time, log_traces, activities)
