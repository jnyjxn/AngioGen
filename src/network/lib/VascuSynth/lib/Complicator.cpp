#include <iostream>
#include <sstream>
#include <fstream>
#include <string.h>
#include <unistd.h>
#include <string>
#include <map>
#include <iterator>
#include <cmath>
#include <vector>
#include <algorithm>
#include <memory>
#include <math.h>

#include "Complicator.h"

using namespace std;

#define arr(arr,x,y,z,dim) *(arr + (z + dim[2]*(y + dim[1]*(x))))

Node::Node() {};
Node::Node(double _x,double _y,double _z) {
		x = _x;
		y = _y;
		z = _z;
};
Node::Node(double* vsVec) {
	x = vsVec[0];
	y = vsVec[1];
	z = vsVec[2];
}
Node::Node(double* vsVec, double _radius) {
		x = vsVec[0];
		y = vsVec[1];
		z = vsVec[2];
		radius = _radius;
}
Node::Node(vector<double> vec) {
		x = vec[0];
		y = vec[1];
		z = vec[2];
};
Node::Node(vector<double> vec, double _radius, double _distanceToRoot, int _parentIndex, int _nodeIndex, int _swcNodeType) {
		x = vec[0];
		y = vec[1];
		z = vec[2];
		radius = _radius;
		distanceToRoot = _distanceToRoot;
		nodeIndex = _nodeIndex;
		if (_parentIndex <= 0){
			parentIndex = -1;
		} else {
			parentIndex = _parentIndex;
		}

		// 0 is normal
		// 5 is bifurcation
		// 6 is terminal
		// 7 is root
		swcNodeType = _swcNodeType;
};

bool Node::operator==(const Node& n) {
		return (x == n.x && y == n.y && z == n.z);
};
Node Node::operator+(const Node& n) {
		return Node(x + n.x,y + n.y, z + n.z);
};
Node Node::operator-(const Node& n) {
		return Node(x - n.x,y - n.y, z - n.z);
};
Node Node::operator*(const double m) {
		return Node(x*m, y*m, z*m);
}

Node Node::reciprocal() {
		return Node(-1/x, -1/y, -1/z);
}
double Node::iter(int dim) {
		if (dim == 0) {
				return x;
		} else if (dim == 1) {
				return y;
		} else if (dim == 2) {
				return z;
		} else {
			return -1.;
		}
};
Node Node::incrementAlongVector(Node direction, double deltaT) {
		// 0 <= deltaT <= 1
		Node newNode;
		newNode.x = x + (direction.x - x)*deltaT;
		newNode.y = y + (direction.y - y)*deltaT;
		newNode.z = z + (direction.z - z)*deltaT;

		return newNode;
};
string Node::str() {
		ostringstream strs;
		strs << x << " " << y << " " << z;
		return strs.str();
};
string Node::str_2() {
		ostringstream strs;
		strs << "Type " << swcNodeType << " Node " << nodeIndex << " (Parent " << parentIndex << "): (" << x << ", " << y << ", " << z << ") - R: " << radius;
		return strs.str();
};
double Node::distanceFromNode(Node n2) {
		return(sqrt( distanceFromNodeSquared(n2)) );
};
double Node::distanceFromNodeSquared(Node n2) {
		return( (n2.x-x)*(n2.x-x) + (n2.y-y)*(n2.y-y) + (n2.z-z)*(n2.z-z) );
};
void Node::calculateDistanceToRoot(Node parentNode) {
		distanceToRoot = parentNode.distanceToRoot + distanceFromNode(parentNode);
};



Segment::Segment() {}
Segment::Segment(vector< Node > _nodes) {
	nodes = _nodes;
}
string Segment::str() {
		ostringstream strs;
		strs << "---------------Segment--------------" << endl;
		for (int i = 0; i < nodes.size(); i++) {
				strs << nodes[i].str_2() << endl;
		}
		return strs.str();
};
int Segment::size() {
		return nodes.size();
};




CatmullRomSpline::CatmullRomSpline() : a(3), b(3), c(3), d(3) {
};
CatmullRomSpline::CatmullRomSpline(Segment s) : a(3), b(3), c(3), d(3) {
		originalSeg = s;
		calculateCoefficients(s);
};

void CatmullRomSpline::calculateCoefficients(Node P0, Node P1, Node P2, Node P3) {
		// Define P(t) = [t^3 t^2 t 1][a b c d]'
		for (int i = 0; i < 3; i++) {
				a[i] = -0.5*P0.iter(i) + 1.5*P1.iter(i) - 1.5*P2.iter(i) + 0.5*P3.iter(i);
				b[i] = P0.iter(i) - 2.5*P1.iter(i) + 2*P2.iter(i) - 0.5*P3.iter(i);
				c[i] = -0.5*P0.iter(i) + 0.5*P2.iter(i);
				d[i] = P1.iter(i);
		};
}
void CatmullRomSpline::calculateCoefficients(Segment s) {
		Node n1;
		Node n2;
		Node n3;
		Node n4;
		if (s.size() == 4) {
			// Full spline - use normally
			n1 = s.nodes[0];
			n2 = s.nodes[1];
			n3 = s.nodes[2];
			n4 = s.nodes[3];
		}
		else if (s.size() == 3) {
			// Terminal branch - extend at the end

		}
		calculateCoefficients(s.nodes[0], s.nodes[1], s.nodes[2], s.nodes[3]);
};

Node CatmullRomSpline::interpolateCRSpline(double t, double radius, int parentIndex, int nodeIndex, int nodeType) {
		vector<double> ans(3);
		for (int i = 0; i < 3; i++) {
				ans[i] = pow(t,3)*a[i] + pow(t,2)*b[i] + t*c[i] + d[i];
		}

		return Node(ans, radius, 0, parentIndex, nodeIndex++, nodeType);
};

pair<Segment,int> CatmullRomSpline::splinifySegment(int refinement, int radiusRule, int parentIndex, int nodeCount, char segmentType[]) {

		double deltaT = 1.0/(refinement-1);

		int mod = segmentType[0] == 'r' ? 0 : 1;

		// -1 is to prevent duplicate nodes
		vector<double> tVals(refinement-mod);
		for (int i = 0; i < tVals.size(); i++) {
			tVals[i] = (i+mod)*deltaT;
		}

		vector<double> radii(tVals.size());

		if (segmentType[0] == 'r') {
			for (int i = 0; i < radii.size(); i++) {
					radii[i] = originalSeg.nodes[2].radius;
			}
		}
		else if (radiusRule == 1) {
				// Inherit radius from root of segment
				for (int i = 0; i < radii.size(); i++) {
						radii[i] = originalSeg.nodes[1].radius;
				}
		} else if (radiusRule == 2) {
				// Linear variation
				double rootRadius = originalSeg.nodes[1].radius;
				double tipRadius = originalSeg.nodes[2].radius;

				radii[0] = rootRadius;
				radii.back() = tipRadius;
				for (int i = 1; i < radii.size() - 1; i++) {
						radii[i] = tVals.at(i)*tipRadius + ( 1.0 - tVals.at(i) )*rootRadius;
				}
		} else if (radiusRule == 3) {
				// Exponential variation
				double rootRadius = originalSeg.nodes[1].radius;
				double tipRadius = originalSeg.nodes[2].radius;

				radii[0] = rootRadius;
				radii.back() = tipRadius;
				for (int i = 1; i < radii.size() - 1; i++) {
						// y = Ae^-b(x-1)
						// rootRadius = A
						// tipRadius = Ae^-b(N-1) = rootRadius e^-b(N-1)
						// b = -log(tipRadius/rootRadius)/(N-1)

						radii[i] = rootRadius*exp( (i-1)*log( tipRadius/rootRadius)/(radii.size()-1) );

				}
		} else if (radiusRule == 4) {
				// Lesion
				double rootRadius = originalSeg.nodes[1].radius;
				double tipRadius = originalSeg.nodes[2].radius;

				int lesionLength = floor( (tVals.size()-2)*rand()/pow(2,32) );
				if (lesionLength < 3) {
						lesionLength = 3;
				}
		}

		vector< Node > output(tVals.size());

		// In order to incorporate parent index, the first node is special
		int nodeType = segmentType[0] == 'r' ? 7 : 0;
		output[0] = interpolateCRSpline(tVals.at(0), radii[0], parentIndex, nodeCount, nodeType);
		nodeCount++;
		for (int i = 1; i < tVals.size() - 1; i++) {
			output[i] = interpolateCRSpline(tVals.at(i), radii[i], nodeCount-1, nodeCount, 0);
			nodeCount++;
		}
		nodeType = segmentType[1] == 't' ? 6 : 5;
		int i = tVals.size() - 1;
		output[i] = interpolateCRSpline(tVals.at(i), radii[i], nodeCount-1, nodeCount, nodeType);
		nodeCount++;

		Segment splinedSegment(output);

		return make_pair(splinedSegment,nodeCount);

};

SplineTree::SplineTree(vector<Segment> _splines){
	splines = _splines;
};

void SplineTree::setOrigin(double originPos[]) {
	for(int i = 0; i < splines.size(); i++) {
		for(int j = 0; j < splines[i].nodes.size(); j++){
			splines[i].nodes[j].x -= originPos[0];
			splines[i].nodes[j].y -= originPos[1];
			splines[i].nodes[j].z -= originPos[2];
		}
	}
}

void SplineTree::scale(double volumeScaleFactor[], double rootRadiusScaleFactor) {
	for(int i = 0; i < splines.size(); i++) {
		for(int j = 0; j < splines[i].nodes.size(); j++){
			splines[i].nodes[j].x = splines[i].nodes[j].x*volumeScaleFactor[0];
			splines[i].nodes[j].y = splines[i].nodes[j].y*volumeScaleFactor[1];
			splines[i].nodes[j].z = splines[i].nodes[j].z*volumeScaleFactor[2];

			splines[i].nodes[j].radius = splines[i].nodes[j].radius*rootRadiusScaleFactor;
		}
	}
}

void SplineTree::rotate(double xAxisAngle,double yAxisAngle,double zAxisAngle) {
		double x = xAxisAngle;
		double y = yAxisAngle;
		double z = zAxisAngle;
		double rot[3][3] = {  {cos(y)*cos(z), -cos(x)*sin(z) + sin(x)*sin(y)*cos(z), sin(x)*sin(z)+cos(x)*sin(y)*cos(z)},
													{cos(y)*sin(z), cos(x)*cos(z) + sin(x)*sin(y)*sin(z), -sin(x)*cos(z) + cos(x)*sin(y)*sin(z)},
													{-sin(y), sin(x)*cos(y), cos(x)*cos(y)}
												};
		for(int i = 0; i < splines.size(); i++) {
			for(int j = 0; j < splines[i].nodes.size(); j++){
				double x_old = splines[i].nodes[j].x;
				double y_old = splines[i].nodes[j].y;
				double z_old = splines[i].nodes[j].z;
				double x_new = rot[0][0]*x_old + rot[0][1]*y_old + rot[0][2]*z_old;
				double y_new = rot[1][0]*x_old + rot[1][1]*y_old + rot[1][2]*z_old;
				double z_new = rot[2][0]*x_old + rot[2][1]*y_old + rot[2][2]*z_old;
				splines[i].nodes[j].x = x_new;
				splines[i].nodes[j].y = y_new;
				splines[i].nodes[j].z = z_new;
			}
		}
}

void SplineTree::printToSWCFile(string filepath) {
	ofstream output;
	stringstream outputSS;

	cout <<"Printing SWC file to " << filepath << endl;

	for(int i = 0; i < splines.size(); i++) {
		for(int j = 0; j < splines[i].nodes.size(); j++){
			Node n = splines[i].nodes[j];

			outputSS << n.nodeIndex << " " << n.swcNodeType << " " << n.x << " " << n.y << " " << n.z << " " << n.radius << " " << n.parentIndex << endl;
		}
	}

	output.open( (filepath).c_str() );
	output<<outputSS.rdbuf()<<endl;

	output.close();
}
