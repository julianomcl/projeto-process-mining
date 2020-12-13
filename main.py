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
CHOICES = '# '


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
    pairs_choices = []
    for activity1, relations in footprint.items():
        for activity2, relation in relations.items():
            if relation == RIGHT_CAUSALITY:
                pairs_causality.add((activity1, activity2))
            if relation == CHOICES:
                if activity1 != activity2:
                    pairs_choices.append((activity1, activity2))
                else:
                    pairs_choices.append((activity1))

    pairs = pairs_causality


    for pair_choices1 in pairs_choices:
        if isinstance(pair_choices1, str):
            pair_choices1 = [pair_choices1]
        for pair_choices2 in pairs_choices:
            if isinstance(pair_choices2, str):
                pair_choices2 = [pair_choices2]
            relation_between_pair = None
            make_pair = True
            intersection = SortedSet(pair_choices1).intersection(pair_choices2)
            pair_choices2 = SortedSet(pair_choices2)
            if len(intersection) != 0:
                for term in intersection:
                    pair_choices2.discard(term)

            if len(pair_choices2) == 0:
                continue
            pair_choices2 = tuple(pair_choices2)

            for activity1 in pair_choices1:
                if not make_pair:
                    break
                for activity2 in pair_choices2:
                    relation = footprint[activity1][activity2]
                    if relation_between_pair is not None and relation_between_pair != relation:
                        make_pair = False
                        break
                    else:
                        relation_between_pair = relation
                    if relation != RIGHT_CAUSALITY:
                        make_pair = False
                        break
            if make_pair:
                if relation_between_pair == RIGHT_CAUSALITY:
                    if len(pair_choices1) == 1:
                        pair_choices1 = pair_choices1[0]
                    if len(pair_choices2) == 1:
                        pair_choices2 = pair_choices2[0]
                    new_pair = (pair_choices1, pair_choices2)
                else:
                    new_pair = (pair_choices2, pair_choices1)
                pairs.add(new_pair)

    print('Xl =', pairs)
    return pairs


# Step 5
def get_maximal_pairs(pairs):
    pos1 = 0
    pair_appended = []
    maximal_pairs = []
    for pair1 in pairs:
        append = True
        flat_pair1 = []
        for s in pair1:
            for e in s:
                flat_pair1.append(e)
        pos2 = 0
        for pair2 in pairs:
            if pos1 != pos2:
                flat_pair2 = []
                for s in pair2:
                    for e in s:
                        flat_pair2.append(e)

                if SortedSet(flat_pair1).issubset(flat_pair2) and SortedSet(flat_pair1) != SortedSet(flat_pair2):
                    append = False
            pos2 = pos2 + 1

        if append:
            if SortedSet(flat_pair1) not in pair_appended:
                maximal_pairs.append(pair1)
                pair_appended.append(SortedSet(flat_pair1))
        pos1 = pos1 + 1

    print('Yl = {', maximal_pairs, '}')
    return maximal_pairs


# Step 6
def get_places(start_activities, end_activities, maximal_pairs):
    places = [('P0', start_activities)]
    place_n = 1
    for pair in maximal_pairs:
        places.append((pair[0], 'P' + str(place_n), pair[1]))
        place_n += 1
    places.append((end_activities, 'P' + str(place_n)))

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


def execute_alpha_miner(traces):
    activities = get_activities(traces)
    start_activities = get_start_activities(traces)
    end_activities = get_end_activities(traces)
    footprint = get_footprint(traces, activities)
    pairs = get_pairs(footprint)
    maximal_pairs = get_maximal_pairs(pairs)
    places = get_places(start_activities, end_activities, maximal_pairs)
    petrinet = get_petrinet(activities, places)
    generate_petrinet_png(petrinet)

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
