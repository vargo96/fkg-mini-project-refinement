from random import shuffle
import types
from ontolearn.concept import Concept


class ELRefinementOperator():

    def __init__(self, knowledge_base):
        self.kb = knowledge_base

    def refine(self, concept):
        """ Refine the given concept depending on its type: Top, Atomic,
            Existential Restriction, Intersection

        Returns:
            Set of refinements
        """
        # Ignore Zinc since owlready2/ontolearn seem to have a problem with it
        #if concept.str.startswith("Zinc"):
        #    return {concept}

        if concept == self.kb.thing:
            return self.refine_thing()
        elif concept.is_atomic:
            return self.refine_atomic(concept)
        elif concept.form == "ObjectSomeValuesFrom":
            return self.refine_existential_restriction(concept)
        elif concept.form == "ObjectIntersectionOf":
            return self.refine_intersection(concept)
            return
        else:
            raise ValueError

    def refine_thing(self):
        """ Refine Top T to direct sub concepts and
            for each object property R in the knowledge base: ∃R.T

        Returns:
            Set of refinements
        """
        thing = self.kb.thing
        refinements = set()
        refinements.update(self.kb.top_down_direct_concept_hierarchy[thing])
        for p in self.kb.property_hierarchy.object_properties:
            refinements.add(self.kb.existential_restriction(thing, p))
        return refinements

    def refine_atomic(self, concept):
        """ Refine the atomic concept C to direct sub concepts and C \sqcap T

        Returns:
            Set of refinements
        """
        refinements = set()
        refinements.update(self.kb.top_down_direct_concept_hierarchy[concept])
        refinements.add(self.kb.intersection(concept, self.kb.thing))
        return refinements

    def refine_existential_restriction(self, concept):
        """ Refine the existential restriction by refining the filler
        
        Returns:
            Set of refinements
        """
        return {self.kb.existential_restriction(ref , concept.role) 
                for ref in self.refine(concept.filler)}

    def refine_intersection(self, concept):
        """Refine intersections by refininf each operand separately and
           adding a refinement every time. 
        
        Returns:
            Set of refinements
        """
        refinements = set()
        refinements.update({self.kb.intersection(concept.concept_a, r) 
                            for r in self.refine(concept.concept_b)})
        refinements.update({self.kb.intersection(r, concept.concept_b) 
                            for r in self.refine(concept.concept_a)})
        return refinements
