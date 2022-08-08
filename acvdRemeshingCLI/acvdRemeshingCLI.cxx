#include "acvdRemeshingCLICLP.h"

#include "acvdRemeshing.h"

#include <iostream>
#include <vector>
#include <string>

namespace
{
  void replaceAll(std::string& str, const std::string& from, const std::string& to) {
    if(from.empty())
        return;
    size_t start_pos = 0;
    while((start_pos = str.find(from, start_pos)) != std::string::npos) {
        str.replace(start_pos, from.length(), to);
        start_pos += to.length();
    }
  }
}

int main( int argc, char * argv[] )
{
  PARSE_ARGS;

  replaceAll(acvdCommand, "$inputModel", inputModel);
  replaceAll(acvdCommand, "$outputModel", outputModel);
  replaceAll(acvdCommand, "$makeNonManifoldMesh", std::to_string((int)makeNonManifoldMesh));
  replaceAll(acvdCommand, "$numberOfVerticesOfMesh", std::to_string(numberOfVerticesOfMesh));
  replaceAll(acvdCommand, "$curvatureOfMesh", std::to_string(curvatureOfMesh));

  std::vector<std::string> commandArguments;
  std::stringstream ss(acvdCommand);
  std::string tmp;
  while(std::getline(ss, tmp, ' ')){
    commandArguments.push_back(tmp);
  }

  int acvdFailed = acvd::acvdRemeshing(commandArguments, &std::cout);

  if (acvdFailed==0){
    std::cout << "<filter-comment>" << "ANTs Apply Transforms " << "</filter-comment>" << std::endl << std::flush;
    std::cout << "<filter-progress>" << 0.99 << "</filter-progress>" << std::endl << std::flush;
    std::cout << "<filter-stage-progress>" << 1.0 << "</filter-stage-progress>" << std::endl << std::flush;
  }

  //std::remove(outputBase.append("InverseComposite.h5").c_str());

  if (acvdFailed){
     return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
