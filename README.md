# FKG - Mini Project

# Foundations of Knowledge Graphs Mini-Project (Group Name: The Pythonistas)

## Group Members (IMT usernames in brackets)

1. Lukas Blübaum (lukasbl)
2. Varun Nandkumar Golani (vngolani)
3. Shivam Sharma (sshivam)


## Motivation
As often done in node classification on knowledge graphs we use the positive and negative
examples to learn concepts in description logics. This way the classifications should not only
be accurate but also explainable by looking at the concept. Atleast for domain experts depending
on the ontology. There are even approaches to verbalize description logics to natural language.
Accordingly, we use a refinement operator for the description logic EL (similar as in the last exercise)
and combine this with a simple greedy approach that traverses the search space. EL only consists of top,
atomic concepts, existential restrictions and intersections.

## Approach 

Our approach consists of the four steps and these are as follows:

1. **Parse the input turtle file:**
    
    In this step, we parse the input turtle file (i.e. `kg-mini-project-train_v2.ttl` or `kg-mini-project-grading.ttl`) and the output contains the set of positive and negative individuals for all learning problems.
   
2. **EL Refinement operator**

    Overview of the different refinement steps depending on the concept type:
- **Thing T**: Refined to direct sub-concepts and for each object property <img src="https://render.githubusercontent.com/render/math?math=r"> in the knowledge base <img src="https://render.githubusercontent.com/render/math?math=\exists r."> T 
- **Atomic concepts** <img src="https://render.githubusercontent.com/render/math?math=C">: Refined to direct sub-concepts and <img src="https://render.githubusercontent.com/render/math?math=C \sqcap "> T 
- **Existential restrictions**: Refined by refining the filler (one new refinement for each refinement of the filler)
- **Intersection**: Refine the operands and add one new refinement for each refinement of the operands
  Refinement steps are pretty similar to the ones in this paper: https://jens-lehmann.org/files/2007/hybrid_learning.pdf

3. **Algorithm**

    We start with the **Thing** concept and do one refinement step. For carcinogenesis this results in Atom, Bond, Compound, ... .
    Afterwards we just follow a simple greedy strategy for a set number of steps (3 as default, since it was enough for the given learning problems). 

    In the first iteration we go through all the refinements of **Thing** and for each we do a refinement step and only keep the best refinement of the resulting set. E.g. we would take Atom do one refinement step and keep the best one, then we would do the same for Bond etc. Afterward, this process continues in the next iteration with the refinements that were found in the first step and so on.

    Best here means which refinement has the highest F1-Score on the train set and the length of a concept is used as a tiebreaker.

4. **Predict and write the result file:**

   The remaining test individuals are then classified with the best concept we found during training of our algorithm (whether the concept en
   tails an individual or not). 
   We receive the predictions of all the individuals for each learning problem and the prediction results are written in a single turtle [result](result.ttl) file.


## Installation
Clone the repository:

```
git clone https://github.com/vargo96/fkg-mini-project.git
```
You might want to create a virtual environment:
```
python -m venv ~/fkg
source ~/fkg/bin/activate
# OR
conda create --name fkg python=3.7.10
conda activate fkg
```
Then run:
```
pip install -r requirements.txt
```

## Reproduce result ttl file:
To reproduce the ```result.ttl``` with the predictions for the remaining individual for each learning problem run:
```
python run.py
```

## Miscellaneous
Some additional usage information for the run script :

```
usage: run.py [-h] [--ontology_path ONTOLOGY_PATH] [--lps_path LPS_PATH]
              [--steps STEPS] [--develop_mode] [--test_ratio TEST_RATIO]
              [--output_file OUTPUT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --ontology_path ONTOLOGY_PATH
                        OWL ontology file.
  --lps_path LPS_PATH
  --steps STEPS         Amount of refinement steps of the algorithm.
  --develop_mode        Set train mode: Split the given learning problems in
                        train and test and evaluate the algorithm.
  --test_ratio TEST_RATIO
                        Ratio of the test split in develop mode.
  --output_file OUTPUT_FILE
```
