/*=========================================================================

	Program: VascuSynth
	Module: $RCSfile: OxygenationMap.cpp,v $
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

#include <iostream>
#include <vector>
#include <fstream>
#include <string>
#include <cstring>
#include <stdlib.h>
#include <cmath>
#include <memory>

#include "MersenneTwister.h"
#include "OxygenationMap.h"
#include "SupplyMap.h"

using namespace std;

// A parametric macro to allow the use of dynamic multi-dimensional arrays
#define arr(arr,x,y,z,dim) *(arr + (z + dim[2]*(y + dim[1]*(x))))

/**
 * constructor, takes the supply map and random seed
 */
OxygenationMap::OxygenationMap(SupplyMap *sMap, int randSeed):rand(){

    supply = sMap;

    int dim[3] = {0,0,0};
  	int myoCentroid[3] = {0,0,0};
  	double myoThickness = 0;

    //if the user specifies a random seed, then seed the mersenne twister
    //random number generator with the seed they have specified.  Otherwise
    //the seed will be somewhat random (the CPU time).
    if (randSeed > 0) {
        long unsigned int a = (long unsigned int) randSeed;
        rand.seed(a);
    }


}

OxygenationMap::~OxygenationMap() {
  delete[] map_d;
  delete[] effectiveMap_d;

  delete supply;
}

/**
 * calculate the sum of the current effective map.  This is used to select
 * a candidate node that has high demand for oxygen.
 */
double OxygenationMap::sum(){
	double acc = 0;

	for(int i = 0; i < dim[0]; i++){
		for(int j = 0; j < dim[1]; j++){
			for(int k = 0; k < dim[2]; k++)
				acc += arr(effectiveMap_d, i, j, k, dim);
		}
	}

	return acc;
}

/**
 * select a candidate terminal node
 */
void OxygenationMap::candidate(double sum, int *cand){
	//MTRand rand;
	double r = rand.rand()*sum;

	double acc = 0;
	for(int i = 0; i < dim[0]; i++){
		for(int j = 0; j < dim[1]; j++){
			for(int k = 0; k < dim[2]; k++){
				acc += arr(effectiveMap_d, i, j, k, dim);
				if(acc >= r){
					cand[0] = i;
					cand[1] = j;
					cand[2] = k;
					return;
				}
			}
		}
	}

	return;
}

/**
 * update the effective map using cand (candidate as a new terminal node
 */
void OxygenationMap::applyCandidate(int cand[]){
  clock_t begin;
  clock_t end;
  double elapsed_secs;

  int temp[3];

  for(int i = 0; i < dim[0]; i++){
    for(int j = 0; j < dim[1]; j++){
      for(int k = 0; k < dim[2]; k++){
        if (arr(effectiveMap_d, i, j, k, dim) <= 0) {
          continue;
        }
        temp[0] = i; temp[1] = j; temp[2] = k;
        arr(effectiveMap_d, i, j, k, dim) *= supply->reduction(cand, temp);
      }
    }
  }
}


/**
 * determine if source is visible from target with respect to
 * the oxygenation map (uses original map - not effective map)
 */
bool OxygenationMap::visible(double source[], double target[]){


	double vect[3];
	vect[0] = target[0] - source[0];
	vect[1] = target[1] - source[1];
	vect[2] = target[2] - source[2];

	double pos[3];
	pos[0] = source[0]; pos[1] = source[1]; pos[2] =  source[2];

	int voxel[3];
	voxel[0] = (int)(source[0]+0.5); voxel[1] = (int)(source[1]+0.5); voxel[2] = (int)(source[2]+0.5);

	int targetVoxel[3];
	targetVoxel[0] =(int)(target[0]+0.5); targetVoxel[1] =(int)(target[1]+0.5); targetVoxel[2] =(int)(target[2]+0.5);

	int i;

	while( !(voxel[0] == targetVoxel[0] && voxel[1] == targetVoxel[1] && voxel[2] == targetVoxel[2]) &&
			!((fabs(pos[0] - target[0]) < 1e-10) && (fabs(pos[1] - target[1]) < 1e-10) && (fabs(pos[2] - target[2]) < 1e-10))){

		double mult = 1e50;
		double dir = 0.5;

		for(i = 0; i < 3; i++){

			if(vect[i] < 0) {
				dir = -0.5;
			} else {
				dir = 0.5;
			}

			double singleMult = fabs((voxel[i]-pos[i] + dir)/vect[i]);


			while (singleMult == 0) {

				// singleMult should always be > 0, this will only present itself as a problem
				// when vect[i] < 0 - where pos[i] moves to x.5 - when it should move to x.5 - c
				// where c is some small positive number

				dir *= 1.000000001;
				singleMult = fabs((voxel[i]-pos[i] + dir)/vect[i]);

			}

			if(singleMult < mult) {
				mult = singleMult;
			}

		}

		for(i = 0; i < 3; i++){
			pos[i] += mult*vect[i];
			voxel[i] = (int)(pos[i]+0.5);
		}

		if(arr(map_d, voxel[0], voxel[1], voxel[2], dim) == 0) {
			return false;
		}

	}

	return true;

}

void OxygenationMap::generateEllipsoidMap(int boundingBox[], int origin[], double mt, double perfPoint[]) {
  // Create a region defined as a quarter ellipsoid centred at some origin
  dim[0] = boundingBox[0]; dim[1] = boundingBox[1]; dim[2] = boundingBox[2];
  map_d = new double[dim[0]*dim[1]*dim[2]]();
  effectiveMap_d = new double[dim[0]*dim[1]*dim[2]]();
  myoCentroid[0] = origin[0]; myoCentroid[1] = origin[1]; myoCentroid[2] = origin[2];
  myoThickness = mt;

  bool validPerfPoint = false;

  int i = 0;
      int j = 0;
      int k = 0;

  int count = 0;
  for(i = 0; i < dim[0]; i++) {
    for(j = 0; j < dim[1]; j++) {
      for(k = 0; k < dim[2]; k++){
        double val =  pow( ( (double)i - origin[0])/((double)dim[0] - origin[0]),2) +
                      pow( ( (double)j - origin[1])/((double)dim[1] - origin[1]),2) +
                      pow( ( (double)k - origin[2])/((double)dim[2] - origin[2]),2);
        if ( val < 1 && val > pow(1 - myoThickness,2)) {
          // dim[2] - k: Flip on x-y plane to put heart in correct orientation
          count++;
          arr(map_d, i, j, dim[2] - k, dim) = 1;
          arr(effectiveMap_d, i, j, dim[2] - k, dim) = 1;

          if (i == (int)perfPoint[0] && j== (int)perfPoint[1] && dim[2] - k == (int)perfPoint[2]) {
            validPerfPoint = true;
          }
        }
      }
    }
  }
  cout << "Myocardium volume (voxels): " << count << endl;

  if (!validPerfPoint) {
    throw string("Perforation point outside myocardium region. Tree generation failed.");
  }
}
