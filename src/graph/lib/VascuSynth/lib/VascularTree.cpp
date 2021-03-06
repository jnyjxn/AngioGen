/*=========================================================================

	Program: VascuSynth
	Module: $RCSfile: VascularTree.cpp,v $
	Language: C++
	Date: $Date: 2011/02/08 10:43:00 $
	Version: $Revision: 1.0 $

Copyright (c) 2011 Medical Imaging Analysis Lab, Simon Fraser University,
British Columbia, Canada.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

* The name of the Insight Consortium, nor the names of any consortium members,
nor of any contributors, may be used to endorse or promote products derived
from this software without specific prior written permission.

* Modified source versions must be plainly marked as such, and must not be
misrepresented as being the original software.

* Free for non-commercial use only.  For commercial use, explicit approval
must be requested by contacting the Authors.

* If you use the code in your work, you must acknowledge it

* Modifications of the source code must also be released as open source

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER AND CONTRIBUTORS ``AS IS''
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

=========================================================================*/

#include <cmath>
#include <iostream>
#include <memory>

#include "VascularTree.h"
#include "OxygenationMap.h"
#include "NodeTable.h"
#include "Complicator.h"

#define PI 3.1415926535897

using namespace std;

/**
 * 	Constructor
 */
VascularTree::VascularTree(OxygenationMap * _oxMap, double _rootRadius,  double* _perf, double _Pperf,
														double _Pterm, double _Qperf, double _rho, double _gamma, double _lambda, double _mu,
														double _minDistance, int _numNodes, int _closestNeighbours, int _randomSeed,
														double* _volumeScaleFactor, int _axialRefinement, double* _myocardiumRotation,
														string _outputFilepath){
	oxMap = _oxMap;
	rootRadius = _rootRadius;
	outputFilepath = _outputFilepath;
	perf = new double[3](); perf[0] = _perf[0]; perf[1] = _perf[1];perf[2] = _perf[2];
	Pperf = _Pperf;
	Pterm = _Pterm;
	Qperf = _Qperf;
	rho = _rho;
	gamma = _gamma;
	lambda = _lambda;
	mu = _mu;
	minDistance = _minDistance;
	mapVoxelWidth = 1;
	Qterm = _Qperf/_numNodes;
	numNodes = _numNodes;
	randomSeed = _randomSeed;
	volumeScaleFactor = new double[3]();
	volumeScaleFactor[0] = _volumeScaleFactor[0];
	volumeScaleFactor[1] = _volumeScaleFactor[1];
	volumeScaleFactor[2] = _volumeScaleFactor[2];
	axialRefinement = _axialRefinement;
	myocardiumRotation = new double[3]();
	myocardiumRotation[0] = _myocardiumRotation[0];
	myocardiumRotation[1] = _myocardiumRotation[1];
	myocardiumRotation[2] = _myocardiumRotation[2];

	closestNeighbours = _closestNeighbours;

	nt.addNode(NodeTable::ROOT, perf, -1, 1, 1, Qperf, -1, -1);
}

VascularTree::~VascularTree(){
	delete[] perf;
	delete[] volumeScaleFactor;
	delete[] myocardiumRotation;

	delete oxMap;
}

/**
 * Calculates the distance between to nodes in the node table.
 */
double VascularTree::distance(int from, int to){
	double* fromPos = nt.getPos(from);
	double* toPos = nt.getPos(to);

	return  sqrt(
				pow(fromPos[0] - toPos[0], 2) +
				pow(fromPos[1] - toPos[1], 2) +
				pow(fromPos[2] - toPos[2], 2))*mapVoxelWidth;
}

double VascularTree::branchLength(int daughterNode) {
	return distance(daughterNode, nt.getParent(daughterNode));
}

vector<double> VascularTree::branchDirection(int daughterNode) {
	double* fromPos = nt.getPos(nt.getParent(daughterNode));
	double* toPos = nt.getPos(daughterNode);

	vector<double> v;
	double mag = 0;

	for (int i = 0; i < 3; i++) {
		double component = toPos[i] - fromPos[i];
		mag += pow(component,2);
	}
	for (int i = 0; i < 3; i++) {
		double component = toPos[i] - fromPos[i];
		v.push_back(component/sqrt(mag));
	}

	return v;
}

/**
 * Calculates the reduced Resistance of segment at id.
 */
void VascularTree::calculateReducedResistance(int id){
	if(nt.getType(id) == NodeTable::TERM){
		double acc = (8.0 * rho * distance(id, nt.getParent(id))/PI);
		nt.setReducedResistance(id, acc);
	} else {
		double acc = 0;
		acc += pow(nt.getLeftRatio(id), 4) / nt.getReducedResistance(nt.getLeftChild(id));
		acc += pow(nt.getRightRatio(id), 4) / nt.getReducedResistance(nt.getRightChild(id));
		acc = 1.0 / acc;
		acc += (8.0 * rho * distance(id, nt.getParent(id))/PI);
		nt.setReducedResistance(id, acc);
	}
}

/**
 * Calculates the ratio of radii of the segment at id.
 */
void VascularTree::calculateRatios(int id){
	int left = nt.getLeftChild(id);
	int right = nt.getRightChild(id);

	double left_over_right = (nt.getFlow(left)*nt.getReducedResistance(left)) / (nt.getFlow(right) * nt.getReducedResistance(right));
	left_over_right = pow(left_over_right, 0.25);

	nt.setLeftRatio(id, pow((1 + pow(left_over_right, -gamma)), (-1.0)/gamma));
	nt.setRightRatio(id, pow((1 + pow(left_over_right, gamma)), (-1.0)/gamma));
}

/**
 * Updates the tree at the bifurication point at id.
 */
void VascularTree::updateAtBifurication(int id, int newChild){
	if(nt.getType(id) != NodeTable::ROOT){
		calculateReducedResistance(newChild);
		calculateRatios(id);

		updateAtBifurication(nt.getParent(id), id);
	} else {
		calculateReducedResistance(newChild);
	}
}

/**
 * Calculates the radii throughout the tree.
 */
void VascularTree::calculateRadius(){
	//the child of the root (perferation) node defines the root segment
	int rootChild = nt.getLeftChild(0);

	originalRootRadius = (nt.getFlow(rootChild) * nt.getReducedResistance(rootChild)) / (Pperf - Pterm);
	originalRootRadius = pow(originalRootRadius, 0.25);
	nt.setRadius(rootChild, originalRootRadius);

	calculateRadius(rootChild);
}

/**
 * Calculates the radius at id.
 */
void VascularTree::calculateRadius(int id){
	if(nt.getType(id) == NodeTable::TERM)
		return;

	int left = nt.getLeftChild(id);
	int right = nt.getRightChild(id);

	nt.setRadius(left, nt.getRadius(id)*nt.getLeftRatio(id));
	nt.setRadius(right, nt.getRadius(id)*nt.getRightRatio(id));

	calculateRadius(left);
	calculateRadius(right);
}

/**
 * Calculates the fitness.
 */
double VascularTree::calculateFitness(){

    //stupid but you have to cast it otherwise it will throw a warning
    int size = (int) nt.nodes.size();
    double acc = 0;

	for(int i = 1; i < size; i++){
		acc += pow(distance(i, nt.getParent(i)), mu) * pow(nt.getRadius(i), lambda);
	}

	return acc;
}

/**
 * When used by local optimization, ignored is the segment to connect to
 * otherwise it should be -1;
 */
bool VascularTree::validateCandidate(double* x0, int ignored){

    //stupid but you have to cast it otherwise it will throw a warning
    int size = (int) nt.nodes.size();

	for(int i = 1; i < size; i++){
		if(i != ignored){
			double distance = pointSegmentDistance(x0, i);
			if(distance < minDistance)
				return false;
		}
	}

	return true;
}

/**
 * Connects the candidate node to a segment through the
 * bifurcation point bifPoint.
 */
void VascularTree::connectPoint(double* point, int segment, double* bifPoint){
	if(nt.getType(segment) == NodeTable::ROOT){
		nt.addNode(NodeTable::TERM, point, segment, 1, 1, Qterm, -1, -1);
		nt.setLeftChild(0, 1);
		nt.setRightChild(0, 1);
		calculateReducedResistance(1);
	} else {
		/* *--- <I_seg> --- *
		//
		//			becomes
		//
		//	*--- <I_bif> --- * ---- < I_con > --- *
		//					 \
		//					  \
		//					  <I_new >
		//						\
		//						 \
		//						  * point[]
		//
		//
		//  where I_sec is replaced with I_con
		//
		//
		// 	I_con = I_seg with the exception of parent (which is set to I_biff
		//  I_seg's parent updates its child to be I_biff
		//  I_new = is a new segment wich is trivially built
		//  I_biff is built using I_new and I_con */

		int biffId = nt.nodes.size();
		int newId = biffId + 1;

		int oldParent = nt.getParent(segment);

		nt.setParent(segment, biffId);
		if(nt.getLeftChild(oldParent) == segment)
			nt.setLeftChild(oldParent, biffId);
		if(nt.getRightChild(oldParent) == segment)
			nt.setRightChild(oldParent, biffId);

		if(oldParent > 0)
			incrementFlow(oldParent, Qterm);

		nt.addNode(NodeTable::BIF, bifPoint, oldParent, 1, 1, nt.getFlow(segment) + Qterm, segment, newId);
		nt.addNode(NodeTable::TERM, point, biffId, 1, 1, Qterm, -1, -1);

		calculateReducedResistance(segment);
		updateAtBifurication(biffId, newId);
	}
}

/**
 * Updates the flow throughout the tree.
 */
void VascularTree::incrementFlow(int parent, double Qterm){
	nt.setFlow(parent, nt.getFlow(parent)+Qterm);
	if(nt.getParent(parent) > 0)
		incrementFlow(nt.getParent(parent), Qterm);
}

/**
 * Returns the distance between a point and a segment.
 */
double VascularTree::pointSegmentDistance(double* x0, int segment){
	double *pos1 = nt.getPos(segment);
	double *pos2 = nt.getPos(nt.getParent(segment));

	double t = -((pos2[0] - pos1[0])*(pos1[0] - x0[0]) +
				 (pos2[1] - pos1[1])*(pos1[1] - x0[1]) +
				 (pos2[2] - pos1[2])*(pos1[2] - x0[2])) /
				((pos2[0] - pos1[0])*(pos2[0] - pos1[0]) +
				 (pos2[1] - pos1[1])*(pos2[1] - pos1[1]) +
				 (pos2[2] - pos1[2])*(pos2[2] - pos1[2]));

	if(t < 0 || t > 1){
		double d1 = pow(pos1[0] - x0[0], 2) + pow(pos1[1] - x0[1], 2) + pow(pos1[2] - x0[2], 2);
		double d2 = pow(pos2[0] - x0[0], 2) + pow(pos2[1] - x0[1], 2) + pow(pos2[2] - x0[2], 2);

		if(d1 < d2)
			return pow(d1, 0.5);
		else
			return pow(d2, 0.5);
	}
	else{
		return  pow(pow((((pos2[0] - pos1[0])*t + pos1[0]) - x0[0]), 2) +
						 pow((((pos2[1] - pos1[1])*t + pos1[1]) - x0[1]), 2) +
						 pow((((pos2[2] - pos1[2])*t + pos1[2]) - x0[2]), 2), 0.5);
	}
}

/**
 * Optimizes the location of a bifurication point for terminal node
 * point and segment 'segment'
 */
double* VascularTree::localOptimization(double * point, int segment, int steps){
	double bestFitness = 1e200;

	double bif[3];
	double perf[3];
	perf[0] = nt.getPos(nt.getParent(segment))[0];
	perf[1] = nt.getPos(nt.getParent(segment))[1];
	perf[2] = nt.getPos(nt.getParent(segment))[2];
	double con[3];
	con[0] = nt.getPos(segment)[0];
	con[1] = nt.getPos(segment)[1];
	con[2] = nt.getPos(segment)[2];

	bif[0] = ((con[0] - perf[0])/2.0 + perf[0]);
	bif[1] = ((con[1] - perf[1])/2.0 + perf[1]);
	bif[2] = ((con[2] - perf[2])/2.0 + perf[2]);

	double stepSize = (((perf[0]+con[0]+point[0])/3.0) - bif[0]+
					   ((perf[1]+con[1]+point[1])/3.0) - bif[1] +
					   ((perf[2]+con[2]+point[2])/3.0) - bif[2])* 2.0 / steps;


	//makesure point is visible from bif - otherwise return null
	if(!oxMap->visible(bif, point) || !inVolume(bif))
		return NULL;

	nt.startUndo();

	connectPoint(point, segment, bif);
	nt.applyUndo();

	double localBest[3];
	double test[3];

	for(int i = 0; i < steps; i++){
		localBest[0] = bif[0]; localBest[1] = bif[1]; localBest[2] = bif[2];
		//try the neighbours of bif (6 connected) as possible new bif points
		//		for a bif point to be valid:
		//			- perf must be visible from bif
		//			- con must be visible from bif
		//			- point must be visilbe from bif
		//			- bif must be a valid candidate (using segment as the ignored)
		//
		//	if the current bif is ever a local optima -search is terminated

		//up
		test[0] = bif[0]+stepSize; test[1] = bif[1]; test[2] = bif[2];
		if(inVolume(test) &&oxMap->visible(perf, test) && oxMap->visible(con, test) && oxMap->visible(point, test) && validateCandidate(test, segment)){
			connectPoint(point, segment, test);
			calculateRadius();
			double fitness = calculateFitness();

			if(fitness < bestFitness){
				localBest[0] = test[0]; localBest[1] = test[1]; localBest[2] = test[2];
				bestFitness = fitness;
			}
		}
		nt.applyUndo();

		//down
		test[0] = bif[0]-stepSize; test[1] = bif[1]; test[2] = bif[2];
		if(inVolume(test) &&oxMap->visible(perf, test) && oxMap->visible(con, test) && oxMap->visible(point, test) && validateCandidate(test, segment)){
			connectPoint(point, segment, test);
			calculateRadius();
			double fitness = calculateFitness();

			if(fitness < bestFitness){
				localBest[0] = test[0]; localBest[1] = test[1]; localBest[2] = test[2];
				bestFitness = fitness;
			}
		}
		nt.applyUndo();

		//left
		test[0] = bif[0]; test[1] = bif[1]+stepSize; test[2] = bif[2];
		if(inVolume(test) &&oxMap->visible(perf, test) && oxMap->visible(con, test) && oxMap->visible(point, test) && validateCandidate(test, segment)){
			connectPoint(point, segment, test);
			calculateRadius();
			double fitness = calculateFitness();

			if(fitness < bestFitness){
				localBest[0] = test[0]; localBest[1] = test[1]; localBest[2] = test[2];
				bestFitness = fitness;
			}
		}
		nt.applyUndo();

		//right
		test[0] = bif[0]; test[1] = bif[1]-stepSize; test[2] = bif[2];
		if(inVolume(test) &&oxMap->visible(perf, test) && oxMap->visible(con, test) && oxMap->visible(point, test) && validateCandidate(test, segment)){
			connectPoint(point, segment, test);
			calculateRadius();
			double fitness = calculateFitness();

			if(fitness < bestFitness){
				localBest[0] = test[0]; localBest[1] = test[1]; localBest[2] = test[2];
				bestFitness = fitness;
			}
		}
		nt.applyUndo();

		//forward
		test[0] = bif[0]; test[1] = bif[1]; test[2] = bif[2]+stepSize;
		if(inVolume(test) &&oxMap->visible(perf, test) && oxMap->visible(con, test) && oxMap->visible(point, test) && validateCandidate(test, segment)){
			connectPoint(point, segment, test);
			calculateRadius();
			double fitness = calculateFitness();

			if(fitness < bestFitness){
				localBest[0] = test[0]; localBest[1] = test[1]; localBest[2] = test[2];
				bestFitness = fitness;
			}
		}
		nt.applyUndo();

		//back
		test[0] = bif[0]; test[1] = bif[1]; test[2] = bif[2]-stepSize;
		if(inVolume(test) &&oxMap->visible(perf, test) && oxMap->visible(con, test) && oxMap->visible(point, test) && validateCandidate(test, segment)){
			connectPoint(point, segment, test);
			calculateRadius();
			double fitness = calculateFitness();

			if(fitness < bestFitness){
				localBest[0] = test[0]; localBest[1] = test[1]; localBest[2] = test[2];
				bestFitness = fitness;
			}
		}
		nt.applyUndo();

		if(localBest[0] != bif[0] || localBest[1] != bif[1] || localBest[2] != bif[2]){
			bif[0] = localBest[0]; bif[1] = localBest[1]; bif[2] = localBest[2];
		} else {
			break;
		}
	}
	nt.clearUndo();
	nt.stopUndo();

	double *ret = new double[4]();
	ret[0] = bif[0]; ret[1] = bif[1]; ret[2] = bif[2];
	ret[3] = bestFitness;
	return ret;
}

/**
 * Determines if point is in the volume.
 */
bool VascularTree::inVolume(double* point){
	if(point[0] < 0 || point[0] >= oxMap->dim[0])
		return false;
	if(point[1] < 0 || point[1] >= oxMap->dim[1])
		return false;
	if(point[2] < 0 || point[2] >= oxMap->dim[2])
		return false;

	return true;
}

/**
 *  Connects the candidate node to the closestNeighbour segments
 *  with an optimized bifurcation location (originally the midpoint of the segment.
 *  The conceptually connected segment that yields the smallest objective
 *  function is elected.
 */
bool VascularTree::connectCandidate(double* point, int steps){

	if(!validateCandidate(point, -1)) {
		return false;	//candiate is too close to an existing segment
	}

	if(nt.nodes.size() == 1){
		if(!oxMap->visible(nt.getPos(0), point)) {
			return false;
		}

		connectPoint(point, 0, NULL);
		return true;
	}

	double best[3];
	bool foundSolution = false;
	double bestFitness = 1e200;
	int bestSegment = 0;

	map<int, double> distances;
	int i;
    int j;

	//determine the distance between the point and each segment
	int size = (int) nt.nodes.size();
    for(i = 1; i < size; i++){
		double d = pointSegmentDistance(point, i);
		distances[i] = d;
	}

	int numCandidates = distances.size();
	int *candidateSegments = new int[numCandidates]();

	//sort the segments by distance
	for(j = 0; j < numCandidates; j++){
		int closest = -1;
		double distance = 1e200;

		map<int, double>::iterator itr;
		for(itr = distances.begin(); itr != distances.end(); itr++){
			double d = itr->second;
			if(d < distance){
				distance = d;
				closest = itr->first;
			}
		}

		if(closest >= 1)
			distances.erase(closest);
		if(closest == -1)
			return false;
		candidateSegments[j] = closest;
	}

	//try the first 'closestNeighbours' segments
	int count = 0;
	double* test;
	for(j = 0; j < numCandidates && count < closestNeighbours; j++){
		test = localOptimization(point, candidateSegments[j], steps);
		if(test != NULL){
			count++;
			if(test[3] < bestFitness){
				best[0] = test[0]; best[1] = test[1]; best[2] = test[2];
				bestSegment = candidateSegments[j];
				bestFitness = test[3];
				foundSolution = true;
			}
		}
		delete[] test;
	}

	delete[] candidateSegments;

	if(!foundSolution)
		return false; //could not connect candidate to ANY segment

	connectPoint(point, bestSegment, best);

	return true;
}

/**
 * iteratively builds a tree by selecting candidate nodes based on an oxygenation demand map
 * and then connecting that candidate node to a series of closest segments at the midpoint of the
 * segment.  The resulting new segment that yields the smallest objective function is selected and
 * added to the tree.  The oxygenation map is updated - reducing values proximal to the candidate node.
 *
 * finally the radii are calcualted recursively by calculating the ratio of the radius of the child over parent,
 * and multiplying that by the radius of the parent to ascertain the radius.
 */
void VascularTree::buildTree(){

	int count = 0;
	double cand[3] = {0.,0.,0.};
	int term[3] = {0,0,0};

	int maxRepeats = 50;
	int numRepeats = 0;
	int minNodes = 3;

	while(count < numNodes && (numRepeats < maxRepeats || count < minNodes)){
		numRepeats++;
		cout << "\r" << "Progress: " << count << "/" << numNodes << flush;

		double sum = oxMap->sum();
		oxMap->candidate(sum, term);

		cand[0] = term[0]; cand[1] = term[1]; cand[2] = term[2];

		if(connectCandidate(cand, 20)){
			count++;
			oxMap->applyCandidate(term);
		}

		if (numRepeats > maxRepeats && count < minNodes) {
			cout << endl;
			throw 1;
		}
	}
	cout << endl;

	calculateRadius();

}

void VascularTree::findAllBranchesFromNode(int from, vector< vector<int> > *tree) {

	// Recursively find all branches from a given node

	// Vectors of pair<segmentIndex,pathDecision>
	//
	// branch is every single possible branch from input node "from"
	// to any terminal
	//
	// longestPath is the branch with the most nodes. If two branches have
	// the same number of nodes, it is selected as the branch with the
	// longest final segment.
	//
	// branchDecision is one of:
	//		l: if this node is the left child of its parent
	//		r: if this node is the right child of its parent

  vector< pair<int, char> > branch;
	vector< pair<int, char> > longestBranch;

	// Add the parent node to the branch
	branch.push_back(make_pair(nt.getParent(from),'P'));

	// branches will be filled with all possible branches from this node
	// inside the printPathsRecur function
	vector< vector< pair<int, char> > > branches;
  printPathsRecur(from, branch, &branches, '0');

	// Loop through branches to find the branch with the most nodes in it
	for ( vector< vector< pair<int, char> > >::size_type i = 0; i < branches.size(); i++ ) {
		if (branches[i].size() > longestBranch.size()) {
			longestBranch = branches[i];
		}
		// If branches have same number of nodes, decide by the length of their final segments
		else if (branches[i].size() == longestBranch.size() &&
			branchLength(branches[i].back().first) > branchLength(longestBranch.back().first)) {
			longestBranch = branches[i];
		}
	}

	// Now take those nodes and add them to the tree
	vector<int> longestBranchNodes;
	for ( vector<int>::size_type j = 0; j < longestBranch.size(); j++ )
	{
		 longestBranchNodes.push_back(longestBranch[j].first);
	}
	tree->push_back(longestBranchNodes);

	// pathway is a list of branchDecision characters
	string pathway = "";
	for ( vector<int>::size_type k = 0; k < longestBranch.size(); k++ )
	{
		 pathway += longestBranch[k].second;
	}

	// Now recursively build the branches from each node of longestBranch,
	// using pathway to take a different route to last time
	for ( vector<int>::size_type l = 0; l < longestBranch.size()-1; l++ )
	{
		// ROOT only has one child so skip it
		if ( nt.getType(longestBranch[l].first) == NodeTable::ROOT) {
			continue;
		}
		else if (pathway[l+1] == 'l') {
			findAllBranchesFromNode(nt.getRightChild(longestBranch[l].first), tree);
		} else if (pathway[l+1] == 'r') {
			findAllBranchesFromNode(nt.getLeftChild(longestBranch[l].first), tree);
		}
	}
}

void VascularTree::printPathsRecur(int node, vector< pair<int, char> > branch, vector< vector< pair<int, char> > > *branches, char direction)
{
	/* append this node to the branch array */
	pair<int, char> nodeStep(node, direction);
	branch.push_back(nodeStep);

  /* it's a leaf, so print the branch that led to here  */
  if (nt.getType(node) == NodeTable::TERM)
  {

		branches->push_back(branch);
	}
  else
  {
    /* try both subtrees */
    printPathsRecur(nt.getLeftChild(node), branch, branches, 'l');

		if (nt.getType(node) != NodeTable::ROOT) {
    	printPathsRecur(nt.getRightChild(node), branch, branches, 'r');
		}
  }
}

SplineTree VascularTree::splinify() {
		vector< vector<int> > tree;
		findAllBranchesFromNode(nt.getLeftChild(0), &tree);

		int currentNodeIndex = 1;

		vector<Segment> fullTree;

		map<int,int> parentIds;

		for ( int i = 0; i < tree.size(); i++ )
		// Each branch
		{
				for ( int j = 0; j < tree.at(i).size() - 1; j++ ) {

						char segmentType[2];

						// Each spline node
						//     x---x---x---x---x
						// o   x---x   o    --> convolve this way
						vector<Node> spline;
						int nodeId;

						// Node 1 (left 'o')
						if (nt.getType(tree.at(i)[j]) != NodeTable::ROOT) {
							segmentType[0] = 'n'; // n for normal initial node

							nodeId = nt.getParent(tree.at(i)[j]);
							spline.push_back(
								Node(
									nt.getPos(nodeId)
								)
							);
						} else {
							segmentType[0] = 'r'; // r for root initial node

							// If segment is root, add a new node at a point along the axis of the segment
							nodeId = tree.at(i)[j];
							double* rootPosTemp = nt.getPos(nodeId);
							vector<double> rootPos(rootPosTemp,rootPosTemp+3);

							nodeId = tree.at(i)[j+1];
							double incrementAmount = -0.1;
							vector<double> newNodePos(3);
							for ( int a = 0; a < newNodePos.size(); a++ ) {
								newNodePos[a] = rootPos[a] + incrementAmount * (branchDirection(nodeId))[a];
							}
							spline.push_back(
								Node(
									newNodePos
								)
							);
						}
						// Node 2 (left 'x')
						nodeId = tree.at(i)[j];
						spline.push_back(
							Node(
								nt.getPos(nodeId),
								nt.getRadius(nodeId)
							)
						);
						// Node 3 (right 'x')
						nodeId = tree.at(i)[j+1];
						spline.push_back(
							Node(
								nt.getPos(nodeId),
								nt.getRadius(nodeId)
							)
						);
						// Node 4 (right 'o')
						if (  nt.getType(tree.at(i)[j+1]) != NodeTable::TERM ) {
							segmentType[1] = 'n'; // n for normal final node

							nodeId = tree.at(i)[j+2];
							spline.push_back(
								Node(
									nt.getPos(nodeId)
								)
							);
						} else {
							segmentType[1] = 't'; // t for terminal final node

							// If segment is terminal, add a new node at a point along the axis of the segment
							nodeId = tree.at(i)[j+1];
							double* rootPosTemp = nt.getPos(nodeId);
							vector<double> rootPos(rootPosTemp,rootPosTemp+3);
							double incrementAmount = 1;
							vector<double> newNodePos(3);
							for ( int a = 0; a < newNodePos.size(); a++ ) {
								newNodePos[a] = rootPos[a] + incrementAmount * (branchDirection(nodeId))[a];
							}
							spline.push_back(
								Node(
									newNodePos
								)
							);
						}

						Segment seg(spline);
						CatmullRomSpline crSpline(seg);

						int parent;

						if ( parentIds.find(tree[i][j]) == parentIds.end() ) {
							parentIds[tree[i][j]] = currentNodeIndex;
							parent = currentNodeIndex - 1;
						} else {
							parent = parentIds[tree[i][j]];
						}

						pair<Segment,int> result = crSpline.splinifySegment(axialRefinement,3,parent,currentNodeIndex,segmentType);

						Segment splinifiedSegment = result.first;
						currentNodeIndex = result.second;

						fullTree.push_back(splinifiedSegment);
				}
		}

		return SplineTree(fullTree);
}
