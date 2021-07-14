from el_refinement import ELRefinementOperator
from ontolearn.base import KnowledgeBase
from random import shuffle
import numpy as np


class FKGMiniProject:

    def __init__(self, ontology_path, terminate_on_goal=False, steps=3):
        self.kb = KnowledgeBase(path=ontology_path)
        self.terminate_on_goal = terminate_on_goal
        self.steps = steps
        self.operator = ELRefinementOperator(self.kb)
        self.all_instances = self.__setup()

    def __setup(self):
        # Get all instances and fix problems in this older version of ontolearn
        instances = set()
        for c in self.kb.concepts.values():
            c.instances = {jjj for jjj in c.owl.instances(world=self.kb.onto.world)} 
            instances.update(c.instances)
        self.kb.thing.instances = instances
        self.kb.thing.owl.namespace = self.kb.onto.get_namespace("http://dl-learner.org/carcinogenesis#")
        return instances


    def cross_validation(self, lp, folds=10):
        """
        Perform k-fold cross-validation on the given learning problem

        Args:
            Learning Problem, number of folds
        Returns:
            Mean F1-Score
        """
        print("Running LP: ", lp['name'])

        pos, neg = self._get_objects_for_iris(lp['pos'], lp['neg'])
        pos = list(pos)
        neg = list(neg)
        shuffle(pos)
        shuffle(neg)
        pos_folds = np.array_split(pos, folds)
        neg_folds = np.array_split(neg, folds)

        f_1 = 0
        for val in range(folds):
            pos_train = np.concatenate(pos_folds[:val] + pos_folds[val+1:])
            neg_train = np.concatenate(neg_folds[:val] + neg_folds[val+1:])
            pos_val = pos_folds[val]
            neg_val = neg_folds[val]

            solution = self._run_algorithm(set(pos_train), set(neg_train))

            val_score_f1 = self._f1(solution[0], set(pos_val), set(neg_val))
            print("Fold ", val+1, " : ", solution[0].str,
                  " - Val score F1: ", val_score_f1,
                  "Train score F1: ", solution[1])

            f_1 += val_score_f1

        print('Mean Score: ', f_1/folds, "\n\n")

    def fit_and_predict(self, lp):
        """
            Trains on the given positive and negative examples and uses the 
            best learned class expression to classify the remaining individuals
            in the knowledge base
        Args:
            Learning problem: Positive and negative examples
        Returns:
            Classification (positive or negative) of the remaning individuals 
            in the knowledge base
        """
        print("Running LP: ", lp['name'])
        pos = lp['pos']
        neg = lp['neg']

        pos_ind, neg_ind = self._get_objects_for_iris(pos, neg)

        solution = self._run_algorithm(pos_ind, neg_ind)
        concept = solution[0]
        print("Found solution: ", concept.str, ' - Train Score: ', solution[1])

        pos_and_neg = pos_ind | neg_ind
        remaining_instances = {inst for inst in self.all_instances if inst not in pos_and_neg}

        pos_classified = concept.instances & remaining_instances
        neg_classified = remaining_instances - pos_classified

        pos_classified = [p.iri for p in pos_classified]
        neg_classified = [n.iri for n in neg_classified]

        print("Classified - Positives: ", len(pos_classified), " Negatives: ", len(neg_classified), "\n")

        return pos_classified, neg_classified

    def _run_algorithm(self, pos, neg):
        """
        Args:
            Positive and negative examples
        Returns:
            Best class expression
        """ 

        current_best = (self.kb.thing, self._f1(self.kb.thing, pos, neg))
        concepts = set()
        for c in self.operator.refine_thing():
            score = self._f1(c, pos, neg)
            if score > 0:
                concepts.add(c) 
            if self.terminate_on_goal and score == 1.0:
                return c, score
            if self._compare_concepts((c, score), current_best):
                current_best = (c, score)

        for _ in range(self.steps):
            temp = set()
            for c in concepts:
                #print("###############")
                #print(c.str)
                refinements = self.operator.refine(c)
                #for r in refinements:
                #    print(r.str, self._f1(r, pos, neg), r.length)
                scores = [(c, self._f1(c, pos, neg)) for c in refinements]
                best = max(scores, key=lambda r: r[1])
                all_best = [x for x in scores if x[1] == best[1]]

                best = min(all_best, key=lambda k: k[0].length)
                if self.terminate_on_goal and best[1] == 1.0:
                    #print(best[1])
                    return best[0], best[1]
                if best[1] > 0:
                    temp.add(best[0])
                if self._compare_concepts(best, current_best):
                    current_best = best
            concepts = temp

        return current_best

    def _f1(self, concept, pos, neg):
        """
        Compute F1-score of the given concept on the positive
        and negative examples

        Returns:
            F1-Score
        """
        instances = concept.instances
        tp = len(instances & pos)
        fp = len(instances & neg)
        fn = len(pos - instances)
        f1 = tp /(tp + 0.5*(fp+fn))
        return round(f1, 3)

    def _compare_concepts(self, c1, c2):
        """
        Compares the two concepts on their F1-score, uses the length as tiebreaker
        in case the score is the same
        Args:
            Two tuples in the form (concept, F1-score)
        Returns:
            True: if c1 is better (higher F1-score or shorter if same score) than c2
            False: otherwise
        """
        return c1[1] > c2[1] or (c1[1] == c2[1] and c1[0].length <= c2[0].length)
    
    def _get_objects_for_iris(self, pos, neg):
        """
        Retrieve the corresponding objects to the IRIs of the positive and negative
        examples

        Args:
            Positive and negative examples
        Returns:
            Positive and negative examples as owlready2 objects
        """
        pos_ind = {self.kb.onto.search(iri=p)[0] for p in pos}
        neg_ind = {self.kb.onto.search(iri=n)[0] for n in neg}
        return pos_ind, neg_ind
