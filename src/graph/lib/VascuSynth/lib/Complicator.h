#ifndef _complicator_h
#define _complicator_h

using namespace std;

#include <sstream>
#include <string.h>
#include <string>
#include <vector>
#include <memory>

class Node {
public:
  double x;
  double y;
  double z;
  double radius;
  double distanceToRoot;
  int    nodeIndex;
  int    parentIndex;
  int    swcNodeType;

  Node();
  Node(double _x,double _y,double _z);
  Node(double* vsVec);
  Node(double* vsVec, double radius);
  Node(vector<double> vec);
  Node(vector<double> vec, double _radius, double _distanceToRoot, int _nodeIndex, int _parentIndex, int _swcNodeType);

  bool operator==(const Node& n);
  Node operator+(const Node& n);
  Node operator-(const Node& n);
  Node operator*(const double m);

  Node reciprocal();
  double iter(int dim);
  Node incrementAlongVector(Node direction, double deltaT);
  Node midpointTo(Node n);
  string str();
  string str_2();
  double distanceFromNode(Node n2);
  double distanceFromNodeSquared(Node n2);
  void calculateDistanceToRoot(Node parentNode);
};

class Segment {
public:
  vector< Node > nodes;

  Segment();
  Segment(vector< Node >);

  void updateNodeIndices(int rootNodeIndex, int nextNodeIndex);

  string str();
  int size();
};

class CatmullRomSpline {
public:
  vector<double> a;
  vector<double> b;
  vector<double> c;
  vector<double> d;
  Segment originalSeg;

  CatmullRomSpline();
  CatmullRomSpline(Segment s);

  void calculateCoefficients(Node P0, Node P1, Node P2, Node P3);
  void calculateCoefficients(Segment s);

  Node interpolateCRSpline(double t, double radius, int nodeIndex, int parentIndex, int nodeType);
  pair<Segment,int> splinifySegment(int refinement, int radiusRule, int parentIndex, int nodeCount, char segmentType[]);
};

class SplineTree {
public:
  vector<Segment> splines;

  SplineTree(vector<Segment> splines);

  void setOrigin(double originPos[]);
  void scale(double volumeScaleFactor[], double rootRadiusScaleFactor);
  void rotate(double xAxisAngle,double yAxisAngle,double zAxisAngle);

  void printToSWCFile(string filepath);
};

#endif
