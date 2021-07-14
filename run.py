import argparse
from fkg_mini_project import FKGMiniProject
from rdflib import Namespace, Graph, Literal, URIRef


NS_CAR = Namespace("http://dl-learner.org/carcinogenesis#")
NS_RES = Namespace("https://lpbenchgen.org/resource/")
NS_PROP = Namespace("https://lpbenchgen.org/property/")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology_path", type=str, default='data/carcinogenesis.owl',
                        help='OWL ontology file.')
    parser.add_argument("--lps_path", type=str, default='data/kg-mini-project-grading.ttl')
    parser.add_argument("--steps", type=int, default=3,
                        help='Amount of refinement steps of the algorithm.')
    parser.add_argument("--terminate_on_goal", action='store_true',
                        help='Stop when the goal (1.0 F1-Score) is found.')
    parser.add_argument("--develop_mode", action='store_true',
                        help='Set develop mode: Run 10-Fold cross validation on the given \
                              learning problems to evaluate the approach.')
    parser.add_argument("--output_file", type=str, default='result.ttl')

    return parser.parse_args()


def parse_lps(lps_path):
    """
    Args:
        Learning problems in .ttl format

    Returns:
        List contaning a dictionary for each learning problem
    """
    lp_instance_list = []
    with open(lps_path, "r") as lp_file:
        for line in lp_file:
            if line.startswith("lpres:"):
                lp_key = line.split()[0].split(":")[1]
            elif line.strip().startswith("lpprop:excludesResource"):
                exclude_resource_list = line.strip()[23:].split(",")
                exclude_resource_list = [individual.replace(";", "")
                                                   .replace("carcinogenesis:",
                                                            "http://dl-learner.org/carcinogenesis#").strip()
                        for individual in exclude_resource_list]
            elif line.strip().startswith("lpprop:includesResource"):
                include_resource_list = line.strip()[23:].split(",")
                include_resource_list = [individual.replace(".", "")
                                                   .replace("carcinogenesis:",
                                                            "http://dl-learner.org/carcinogenesis#").strip()
                        for individual in include_resource_list]
                lp_instance_list.append({"name": lp_key,
                                         "pos": include_resource_list,
                                         "neg": exclude_resource_list})

    return lp_instance_list


def add_lp_to_graph(graph, lp_name, pos, neg, index):
    """ Add the given learning problem together with positive and negative classified
        individuals for that lp to the graph (Format as specified in the slides)

    Args:
        Learning problem name, positive and negative classifications
        for that learning problem
    """
    current_pos = f'result_{index}pos'
    current_neg = f'result_{index}neg'
    graph.add((URIRef(NS_RES + current_pos), NS_PROP.belongsToLP, Literal(True)))
    graph.add((URIRef(NS_RES + current_pos), NS_PROP.pertainsTo, URIRef(NS_RES + lp_name)))

    for p in pos:
        graph.add((URIRef(NS_RES + current_pos), NS_PROP.resource, URIRef(p)))

    graph.add((URIRef(NS_RES + current_neg), NS_PROP.belongsToLP, Literal(False)))
    graph.add((URIRef(NS_RES + current_neg), NS_PROP.pertainsTo, URIRef(NS_RES + lp_name)))

    for n in neg:
        graph.add((URIRef(NS_RES + current_neg), NS_PROP.resource, URIRef(n)))


def run(args):
    """ Run the algorithm for the given learning problem either in develop mode
        or predict mode (training on lps and classifying remaining individuals)
    Args:
        Command line arguments
    """
    lps = parse_lps(args.lps_path)
    project = FKGMiniProject(args.ontology_path, 
                             terminate_on_goal=args.terminate_on_goal,
                             steps=args.steps)

    if args.develop_mode:
        for lp in lps:
            project.cross_validation(lp)
    else:
        g = Graph()
        g.bind('carcinogenesis', NS_CAR)
        g.bind('lpres', NS_RES)
        g.bind('lpprop', NS_PROP)

        for idx, lp in enumerate(lps):
            pos, neg = project.fit_and_predict(lp)
            add_lp_to_graph(g, lp['name'], pos, neg, idx+1)

        g.serialize(destination='result.ttl', format='turtle')

if __name__ == '__main__':
    run(parse_args())
