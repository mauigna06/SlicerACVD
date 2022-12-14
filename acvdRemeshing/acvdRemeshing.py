import logging
import os

import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


#
# acvdRemeshing
#

class acvdRemeshing(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "acvdRemeshing"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#acvdRemeshing">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """"""

#
# acvdRemeshingWidget
#

class acvdRemeshingWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/acvdRemeshing.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = acvdRemeshingLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).
        self.ui.inputModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.outputModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.numberOfVerticesOfMeshSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.curvatureOfMeshSlideWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.invertOutputCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
        
        # Buttons
        self.ui.runRemeshingButton.connect('clicked(bool)', self.onRunRemeshingButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.inputModelSelector.setCurrentNode(self._parameterNode.GetNodeReference("inputModel"))
        self.ui.outputModelSelector.setCurrentNode(self._parameterNode.GetNodeReference("outputModel"))
        self.ui.numberOfVerticesOfMeshSliderWidget.value = int(self._parameterNode.GetParameter("numberOfVerticesOfMesh"))
        self.ui.curvatureOfMeshSliderWidget.value = float(self._parameterNode.GetParameter("curvatureOfMesh"))
        self.ui.nonManifoldMeshCheckBox.checked = self._parameterNode.GetParameter("nonManifoldMesh") == "True"
        
        self.ui.inputModelSelector.toolTip = "Model to be remeshed."
        self.ui.outputModelSelector.toolTip = "Remeshed output model."
        self.ui.numberOfVerticesOfMeshSliderWidget.toolTip = "Select the target number of vertices the output mesh will have."
        self.ui.numberOfVerticesOfMeshSliderWidget.toolTip = "Select the target curvature the output mesh will have."

        self.ui.runRegistrationButton.enabled = (self.ui.inputModelSelector.currentNodeID != ""
          and self.ui.outputModelSelector.currentNodeID != "")

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetNodeReferenceID("inputModel", self.ui.inputModelSelector.currentNodeID)
        self._parameterNode.SetNodeReferenceID("outputModel", self.ui.outputModelSelector.currentNodeID)
        self._parameterNode.SetParameter("numberOfVerticesOfMesh", str(self.ui.numberOfVerticesOfMeshSliderWidget.value))
        self._parameterNode.SetParameter("curvatureOfMesh", str(self.ui.curvatureOfMeshSliderWidget.value))
        self._parameterNode.SetParameter("nonManifoldMesh", "True" if self.ui.nonManifoldMeshCheckBox.checked else "False")
        
        self._parameterNode.EndModify(wasModified)

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):
            # Compute output
            self.logic.process(self.ui.inputModelSelector.currentNode(), self.ui.outputModelSelector.currentNode(),
                               self.ui.numberOfVerticesOfMeshSliderWidget.value, self.ui.invertOutputCheckBox.checked)

    def onRunRemeshingButton(self):
        if self.ui.runRegistrationButton.text == 'Cancel':
        self.logic.cancelRegistration()
            return

        parameters = {}
        
        parameters['outputSettings'] = {}
        parameters['outputSettings']['transform'] = self.ui.outputTransformComboBox.currentNode()
        parameters['outputSettings']['volume'] = self.ui.outputVolumeComboBox.currentNode()
        parameters['outputSettings']['interpolation'] = self.ui.outputInterpolationComboBox.currentText
        parameters['outputSettings']['useDisplacementField'] = int(self.ui.outputDisplacementFieldCheckBox.checked)

        parameters['initialTransformSettings'] = {}
        parameters['initialTransformSettings']['initializationFeature'] = int(self._parameterNode.GetParameter("initializationFeature"))
        parameters['initialTransformSettings']['initialTransformNode'] = self.ui.initialTransformNodeComboBox.currentNode()

        parameters['generalSettings'] = {}
        parameters['generalSettings']['dimensionality'] = self.ui.dimensionalitySpinBox.value
        parameters['generalSettings']['histogramMatching'] = int(self.ui.histogramMatchingCheckBox.checked)
        parameters['generalSettings']['winsorizeImageIntensities'] = [self.ui.winsorizeRangeWidget.minimumValue, self.ui.winsorizeRangeWidget.maximumValue]
        parameters['generalSettings']['computationPrecision'] = self.ui.computationPrecisionComboBox.currentText

        self.logic.process(**parameters)

        self.ui.cliWidget.setCurrentCommandLineModuleNode(self.logic._cliNode)
        self._cliObserver = self.logic._cliNode.AddObserver('ModifiedEvent', self.onProcessingStatusUpdate)
        self.ui.runRegistrationButton.text = 'Cancel'

    def onProcessingStatusUpdate(self, caller, event):
        if (caller.GetStatus() & caller.Cancelled):
        self.ui.runRegistrationButton.text = "Run Registration"
        self.logic._cliNode.RemoveObserver(self._cliObserver)
        elif (caller.GetStatus() & caller.Completed):
        if (caller.GetStatus() & caller.ErrorsMask):
            qt.QMessageBox().warning(qt.QWidget(),'Error', 'ANTs Failed. See CLI output.')
        self.ui.runRegistrationButton.text = "Run Registration"
        self.logic._cliNode.RemoveObserver(self._cliObserver)
        else:
        self.ui.runRegistrationButton.text = "Cancel"


#
# acvdRemeshingLogic
#

class acvdRemeshingLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")

    def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time
        startTime = time.time()
        logging.info('Processing started')

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            'InputVolume': inputVolume.GetID(),
            'OutputVolume': outputVolume.GetID(),
            'ThresholdValue': imageThreshold,
            'ThresholdType': 'Above' if invert else 'Below'
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')


#
# acvdRemeshingTest
#

class acvdRemeshingTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_acvdRemeshing1()

    def test_acvdRemeshing1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData
        registerSampleData()
        inputVolume = SampleData.downloadSample('acvdRemeshing1')
        self.delayDisplay('Loaded test data set')

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = acvdRemeshingLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay('Test passed')
