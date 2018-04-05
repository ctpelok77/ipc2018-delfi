#ifndef HELPERS_H
#define HELPERS_H

#include "state.h"
#include "variable.h"
#include "successor_generator.h"
#include "causal_graph.h"

#include <string>
#include <vector>
#include <iostream>

using namespace std;

class State;
class MutexGroup;
class Operator;
class Axiom;
class DomainTransitionGraph;

//void read_everything
void read_preprocessed_problem_description(istream &in,
                                           bool &metric,
                                           vector<Variable> &internal_variables,
                                           vector<Variable *> &variables,
                                           vector<MutexGroup> &mutexes,
                                           State &initial_state,
                                           vector<pair<Variable *, int> > &goals,
                                           vector<Operator> &operators,
                                           vector<Axiom> &axioms);

//void dump_everything
void dump_preprocessed_problem_description(const vector<Variable *> &variables,
                                           const State &initial_state,
                                           const vector<pair<Variable *, int> > &goals,
                                           const vector<Operator> &operators,
                                           const vector<Axiom> &axioms);

void dump_DTGs(const vector<Variable *> &ordering,
               vector<DomainTransitionGraph> &transition_graphs);
void generate_unsolvable_cpp_input();
void generate_cpp_input(bool causal_graph_acyclic,
                        const vector<Variable *> &ordered_var,
                        const bool &metric,
                        const vector<MutexGroup> &mutexes,
                        const State &initial_state,
                        const vector<pair<Variable *, int> > &goals,
                        const vector<Operator> &operators,
                        const vector<Axiom> &axioms,
                        const SuccessorGenerator &sg,
                        const vector<DomainTransitionGraph> transition_graphs,
                        const CausalGraph &cg);
void check_magic(istream &in, string magic);

void write_mutexes(vector<Variable*> & variables, vector<MutexGroup> & m, string filename);
void write_mutexes(vector<Variable*> & variables, vector<MutexGroup> & m, ofstream & filename);
void write_operators(vector<Operator> & ops, string filename);
void write_operators(vector<Operator> & ops, ofstream & filename);
void write_variables(vector<Variable *> & variables, string filename);
void write_variables(vector<Variable *> & variables, ofstream & file);

#endif
