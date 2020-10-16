/*=========================================================================

   Program: VascuSynth
   Module: $RCSfile: VascuSynth.cpp,v $
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

//commands for mkdir
#ifdef _WIN32
#include "direct.h"
#else
#include <sys/types.h>
#include <sys/stat.h>
#endif

#include <iostream>
#include <unistd.h>
#include <sstream>
#include <fstream>
#include <string>
#include <map>
#include <iterator>
#include <cmath>
#include <vector>
#include <algorithm>
#include <ctime>
#include <memory>

using namespace std;

/**
 * Utility function to read a text file and store the lines into a vector
 * that is returned.  This way we do not have to have a bunch of files open at
 * the same time.
 * @param const char* filename the filename to read
 * @return vector<string> a vector of file lines from the file
 * @throws string exception if the file cannot be read
 */
vector<string> readFileLines(const char * filename){

		ifstream oFile;
		oFile.open(filename, ios::in);
		vector<string> lines;
		string line;

		if(oFile.is_open()) {

				while(!oFile.eof()) {
						getline(oFile, line);
						string copy = line;
						if (!copy.empty()) {
								lines.push_back(copy);
						}
				}

				oFile.close();

		} else {
				throw "Could not open file " + ( (string) filename);
		}

		return lines;

}


#include "OxygenationMap.h"
#include "SupplyMap.h"
#include "VascularTree.h"
#include "Complicator.h"
#include "OptionParser.h"



/**
 * make dir that is cross platform
 */
int mmkdir(const char * dirname) {
#ifdef _WIN32
		return mkdir(dirname);
#else
		return mkdir(dirname, 0777);
#endif
}

/**
 * itoa is non standard so define it and use it,
 * converts an integer to a string
 */
string itoa(int value, int base) {

		string buf;

		// check that the base if valid
		if (base < 2 || base > 16) return buf;

		enum { kMaxDigits = 35 };
		buf.reserve( kMaxDigits );  // Pre-allocate enough space.

		int quotient = value;

		// Translating number to string with base:
		do {
				buf += "0123456789abcdef"[ (int) std::abs( quotient % base ) ];
				quotient /= base;
		} while ( quotient );

		// Append the negative sign
		if ( value < 0) buf += '-';

		reverse( buf.begin(), buf.end() );
		return buf;
}

enum optionIndex {
	UNKNOWN,
	HELP,
	ROOT_RADIUS,
	ANGLE_MODE,
	BOUNDING_BOX,
	MYOCARDIUM_ROTATION,
	MYOCARDIUM_THICKNESS,
	PERF_PRESSURE,
	TERM_PRESSURE,
	PERF_FLOW,
	RHO,
	GAMMA,
	LAMBDA,
	MU,
	MIN_DISTANCE,
	NUM_NODES,
	CLOSEST_NEIGHBOURS,
	RANDOM_SEED,
	AXIAL_REFINEMENT,
	SAVE_TO
};

void confirmAllArgsExist(const option::Option* options) {
	vector<string> missingItems;

	if (!options[ROOT_RADIUS])
		missingItems.push_back("--rr");
	if (!options[ANGLE_MODE])
		missingItems.push_back("--am");
	if (!options[BOUNDING_BOX])
		missingItems.push_back("--bb");
	if (!options[MYOCARDIUM_ROTATION])
		missingItems.push_back("--mr");
	if (!options[MYOCARDIUM_THICKNESS])
		missingItems.push_back("--mt");
	if (!options[PERF_PRESSURE])
		missingItems.push_back("--pp");
	if (!options[TERM_PRESSURE])
		missingItems.push_back("--tp");
	if (!options[PERF_FLOW])
		missingItems.push_back("--pf");
	if (!options[RHO])
		missingItems.push_back("--r");
	if (!options[GAMMA])
		missingItems.push_back("--g");
	if (!options[LAMBDA])
		missingItems.push_back("--l");
	if (!options[MU])
		missingItems.push_back("--m");
	if (!options[MIN_DISTANCE])
		missingItems.push_back("--md");
	if (!options[NUM_NODES])
		missingItems.push_back("--nn");
	if (!options[CLOSEST_NEIGHBOURS])
		missingItems.push_back("--cn");
	if (!options[RANDOM_SEED])
		missingItems.push_back("--rs");
	if (!options[AXIAL_REFINEMENT])
		missingItems.push_back("--ar");
	if (!options[SAVE_TO])
		missingItems.push_back("--op");

	if (missingItems.size() > 0) {
		cout << "Missing the following arguments: ";
		for (vector<string>::iterator it = missingItems.begin(); it != missingItems.end(); it++) {
			cout << *it << ", ";
		}
		cout << endl;

		throw 2;
	}
}

void splitTripleItemIntoArray(string itemString, double* output) {
	itemString.erase(
	    remove( itemString.begin(), itemString.end(), '\"' ),
	    itemString.end()
    );
	itemString.erase(
	    remove( itemString.begin(), itemString.end(), '\'' ),
	    itemString.end()
    );

	int spacePosition = itemString.find(" ");
	string pointvalue = itemString.substr(0, spacePosition);
	output[0] = atof(pointvalue.c_str());

	int spacePosition2 = itemString.find(" ", spacePosition+1);
	pointvalue = itemString.substr(spacePosition+1, spacePosition2);
	output[1] = atof(pointvalue.c_str());

	pointvalue = itemString.substr(spacePosition2+1);
	output[2] = atof(pointvalue.c_str());
}

void splitTripleItemIntoArray(string itemString, int* output) {
	itemString.erase(
	    remove( itemString.begin(), itemString.end(), '\"' ),
	    itemString.end()
    );
	itemString.erase(
	    remove( itemString.begin(), itemString.end(), '\'' ),
	    itemString.end()
    );

	int spacePosition = itemString.find(" ");
	string pointvalue = itemString.substr(0, spacePosition);
	output[0] = atoi(pointvalue.c_str());

	int spacePosition2 = itemString.find(" ", spacePosition+1);
	pointvalue = itemString.substr(spacePosition+1, spacePosition2);
	output[1] = atoi(pointvalue.c_str());

	pointvalue = itemString.substr(spacePosition2+1);
	output[2] = atoi(pointvalue.c_str());
}

/**
 *  Reads the parameters from the parameter file and then builds
 *  the vascular structure in the form of a tree
 */
VascularTree * buildTree(const option::Option* options){
		try {
			confirmAllArgsExist(options);
		}
		catch (int c) {
			throw c;
		}

		SupplyMap * sm = NULL;
		OxygenationMap * om = NULL;

		string angleMode = (string) options[ANGLE_MODE].arg;
		double rootRadius = atof(options[ROOT_RADIUS].arg);

		double boundingBox[3];
		splitTripleItemIntoArray(options[BOUNDING_BOX].arg, boundingBox);

		double myocardiumRotation[3];
		splitTripleItemIntoArray(options[MYOCARDIUM_ROTATION].arg, myocardiumRotation);

		double myoThickness = atof(options[MYOCARDIUM_THICKNESS].arg);
		double pperf = atof(options[PERF_PRESSURE].arg);
		double pterm = atof(options[TERM_PRESSURE].arg);
		double qperf = atof(options[PERF_FLOW].arg);
		double rho = atof(options[RHO].arg);
		double gamma = atof(options[GAMMA].arg);
		double lambda = atof(options[LAMBDA].arg);
		double mu = atof(options[MU].arg);
		double minDistance = atof(options[MIN_DISTANCE].arg);
		int numNodes = atoi(options[NUM_NODES].arg);
		int closestNeighbours = atoi(options[CLOSEST_NEIGHBOURS].arg);
		int randomSeed = atoi(options[RANDOM_SEED].arg);
		int axialRefinement = atoi(options[AXIAL_REFINEMENT].arg);
		string saveTo = options[SAVE_TO].arg;

		int found = saveTo.find_last_of("/\\");
		if (found >= 1) {
			string rootDirectory = saveTo.substr(0,found);

			mmkdir(rootDirectory.c_str());
		}

		//filter out the /r that appears at times and messes up the directory name
		if (saveTo[ saveTo.length() - 1 ] == '\r') {
				saveTo = saveTo.substr(0, saveTo.length()-1);
		}

		if (angleMode == "d" || angleMode == "degree") {
			for (int i = 0; i < 3; i++) {
				myocardiumRotation[i] *= 0.0174533;
			}
		}

		int omapBoundingBox[3] = {256, 512, 512}; // It works
		double perf[3] = {238, 256, 512}; // It also works
		int myoCentroid[3] = {0, 256, 0};

		//load the supply map
		sm = new SupplyMap();
		sm->generateMap(omapBoundingBox);

		//load the oxygenation map
		om = new OxygenationMap(sm, randomSeed);
		try {
					om->generateEllipsoidMap(omapBoundingBox, myoCentroid, myoThickness, perf);
		} catch (char * str) {
					throw (string) str;
		}
		om->supply = sm;

		double volumeScaleFactor[3] = {1,1,1};
		for (int a = 0; a < 3; a++) {
			volumeScaleFactor[a] = boundingBox[a]/omapBoundingBox[a];
		}

		VascularTree *vt = new VascularTree(om, rootRadius, perf, pperf, pterm, qperf, rho, gamma, lambda, mu, minDistance, numNodes, closestNeighbours,
											randomSeed, volumeScaleFactor, axialRefinement, myocardiumRotation, saveTo);

		try {
			vt->buildTree();
		}
		catch (int e) {
			throw e;
		}

		return vt;
}

const option::Descriptor usage[] =
{
	{UNKNOWN, 				0,"" , "",option::Arg::None, "USAGE: example [options]\n\nOptions:" },
	{HELP,    				0,"h", "help",option::Arg::None, "  --help  \tPrint usage and exit." },
	{ROOT_RADIUS,    		1,"" , "rr",option::Arg::NonEmpty, "  --rr  \tRadius of root node." },
	{ANGLE_MODE,    		2,"" , "am",option::Arg::NonEmpty, "  --am  \tEither degree: 'd', or radian: 'r'." },
	{BOUNDING_BOX,    		3,"" , "bb",option::Arg::NonEmpty, "  --bb  \tThe bounding cuboid, w*d*h, defined as 3 integers e.g. '200 200 200'." },
	{MYOCARDIUM_ROTATION, 	4,"" , "mr",option::Arg::NonEmpty, "  --mr  \tRotation of the heart defined as 3 rotations around the axes x, y, z eg '20 -4 9'." },
	{MYOCARDIUM_THICKNESS,  5,"" , "mt",option::Arg::NonEmpty, "  --mt  \tThickness of the myocardium with 0 being infinitely thin-walled and 1 being fully dense (no ventricles)." },
	{PERF_PRESSURE,    		6,"" , "pp",option::Arg::NonEmpty, "  --pp  \tStatic pressure at the inlet." },
	{TERM_PRESSURE,    		7,"" , "tp",option::Arg::NonEmpty, "  --tp  \tStatic pressure at all outlets." },
	{PERF_FLOW,    			8,"" , "pf",option::Arg::NonEmpty, "  --pf  \tFlow rate at the inlet." },
	{RHO,    				9,"" , "r",option::Arg::NonEmpty, "  --r  \tDensity of the blood." },
	{GAMMA,    				10,"", "g",option::Arg::NonEmpty, "  --g  \tRatio of left-branching vs right-branching." },
	{LAMBDA,    			11,"", "l",option::Arg::NonEmpty, "  --l  \tHigher lambda results in narrower vessels." },
	{MU,    				12,"", "m",option::Arg::NonEmpty, "  --m  \tHigher lambda results in shorter vessels." },
	{MIN_DISTANCE,    		13,"", "md",option::Arg::NonEmpty, "  --md  \tMinimum distance between two nodes." },
	{NUM_NODES,    			14,"", "nn",option::Arg::NonEmpty, "  --nn  \tThe number of nodes (bifurcations + termini) to generate." },
	{CLOSEST_NEIGHBOURS,    15,"", "cn",option::Arg::NonEmpty, "  --cn  \tNumber of closest nodes during candidate attachment selection." },
	{RANDOM_SEED,    		16,"", "rs",option::Arg::NonEmpty, "  --rs  \tSeed for random number generation." },
	{AXIAL_REFINEMENT,    	17,"", "ar",option::Arg::NonEmpty, "  --ar  \tNumber of sub-segments during splinification." },
	{SAVE_TO,    			18,"", "op",option::Arg::NonEmpty, "  --op  \tPath for output file." },
	{0,0,0,0,0,0}
};

/**
 * VascuSynth: takes a series of parameters
 * and generates a vascular structure based on the parameters.  Information about
 * the vascular structure is saved as
 * a SWC file.
 */
int main(int argc, char* argv[]){
		clock_t begin = clock();

	  argc-=(argc>0); argv+=(argc>0); // skip program name argv[0] if present
	  option::Stats  stats(usage, argc, argv);
	  option::Option options[stats.options_max], buffer[stats.buffer_max];
	  option::Parser parse(usage, argc, argv, options, buffer);

	  if (parse.error())
	    return 1;

		if (options[HELP] || argc == 0) {
	    option::printUsage(std::cout, usage);
	    return 0;
	  }

		VascularTree * vt = NULL;
		//build the tree
		try {
			VascularTree * vt = buildTree(options);

			clock_t end = clock();
			double elapsed_secs = double(end - begin) / CLOCKS_PER_SEC;
			cout << "The vascular tree has been built sucessfully in " << elapsed_secs << " seconds..." << endl;

			double rootRadiusScaleFactor = vt->rootRadius/vt->originalRootRadius;

			SplineTree st = vt->splinify();
			st.setOrigin(vt->perf);
			st.scale(vt->volumeScaleFactor,rootRadiusScaleFactor);
			st.rotate(vt->myocardiumRotation[0],vt->myocardiumRotation[1],vt->myocardiumRotation[2]);
			st.printToSWCFile(vt->outputFilepath);

			delete vt;

			cout << "[compsuccess]" << endl;
		}
		catch (int c) {
			delete vt;

			if (c==1) {
				cout << "[paramfail]" << endl;
			}
			return c;
		}


		return 0;
}
