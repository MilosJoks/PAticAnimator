import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.markers as mmarkers
import matplotlib.gridspec as mgs

from matplotlib.transforms import Affine2D
from matplotlib.cm import ScalarMappable

import os
import shutil
import imageio.v3 as iio

import datetime

class PAticAnimator:
    '''
    Class for animating the time evolution of the order parameter phase field.

    The structure of the class is based around the phase field array, which is the one parameter
    on which the class makes a hard requirement in that it must be given as a 3D array with shape
    (nt,ny,nx), where nt is the number of time steps in the evolution - or in the context of the
    animation, the number of frames - while nx and ny are the number of points along each of the
    coordinate axes. These parameters are used to construct the coordinate grids for the plots,
    as well as the animation itself.

    Apart from these requirements, the class is made to be fairly flexible in terms of how the data
    is handled - in what order the various parameters can be given and in what format, and also in
    terms of plot design, allowing for styling the phase field colormap and transparency, order
    parameter marker type, marker color, marker size, and more.

    Initialization

    Positional arguments:
        p: int
            Determines what kind of p-atic the animator will be animating. Used to determine the
            correct marker for the order parameter plots.

    Keyword arguments:
        field: 3D array || (default: None)
            Phase field data used to draw the frames of the animation, as well as to determine
            the size of the coordinate grids.

            The phase field array can be updated with the class method set_phi (details below) at
            any point up until the call to make the animation is made.

        x, y: tuple, list, array || (default: None)
            The coordinate grids can be set by giving the animator a tuple or list containing the
            upper and lower limits for the respective coordinate axes.

            Alternatively, the grids can also be set with 1D or 2D arrays. Unless the array shapes
            match that of the phase field array along the last two axes, the animator will
            construct a brand new grid using the max and min values from the supplied arrays as the
            axis limits for the respective coordinate.

            If only one of the coordinates is given, then both coordinates will automaically be set
            to the same values.

            If the coordinates are given, but the phase field array isn't, then the animator will
            only extract the limits of the coordinate axes, discarding the rest of the input data.
            The full coordinate grid will then be constructed from the limits once the phase field
            array is supplied.

            If no coordinates are given, but the phase field array is given, then the animator will
            automatically construct a default grid on the unit [0,1]x[0,1] square.

            The coordinate grids can be updated with the class method set_grid (details below) at any
            point up until the call to make the animation is made.

    Class Attributes
        p: int
            The degree of the p-atic order parameter. Used to determine the correct marker type for
            the order parameter plots.

        x0: float || (default: None)
            Lower limit of the x-coordinate in the coordinate grid.

        x1: float || (default: None)
            Upper limit of the x-coordinate in the coordinate grid.

        nx: int || (default: None)
            Number of points in the grid along the x-axis. Determined by the shape of the phase
            field array.

        x: 2D array || (default: None)
           x-coordinate grid. Defaults to None until the coordinate grid is fully constructed as
           described above (see also the set_grid class method).

        y0: float || (default: None)
            Lower limit of the y-coordinate in the coordinate grid.

        y1: float || (default: None)
            Upper limit of the y-coordinate in the coordinate grid.

        ny: int || (default: None)
            Number of points in the grid along the y-axis. Determined by the shape of the phase
            field array.

        nt: int || (default: None)
            Number of time steps in the time evolution of the phase field. Determined by the
            shape of the phase field array.

        y: 2D array || (default: None)
           y-coordinate grid. Defaults to None until the coordinate grid is fully constructed as
           described above (see also the set_grid class method).

        field: 3D array || (default: None)
            Phase field array.

        which: str || 'pf' | 'op' | 'both' | (default: 'pf')
            Determines which of the phase field and order parameter to plot.
              'pf' - phase field,
              'op' - order parameter,
            'both' - phase field and order parameter.

        grouping: str || 'separate' | 'together' | (default: 'together')
            Determines how the order parameter and phase field are to be grouped in the figure.
            Only affects the plot if the which attribute is set to 'both', otherwise grouping is
            ignored.
            'separate' - plots the phase field and order parameter in each their own axes in the
                         figure,
            'together' - plots the phase field and order parameter in the same axes.

        mode: int || 0 | 1 | 2 | (default: 0)
            Determines the plot style if the phase field and order parameter are plotted together,
            in other words, when the which attribute is set to 'both' and the grouping attribute is
            set to 'together'. Otherwise, mode is ignored.
            0 - plots the order parameter in solid color over the phase field contour plot,
            1 - plots the order parameter with markers color mapped by the appropriate value of the
                phase field over a solid background,
            2 - plots the order parameter with markers color mapped by the appropriate value of the
                phase field over a semi-transparent phase field contour plot.

        fig: Matplotlib figure
            The figure where the plot is drawn. This attribute can be manipulated just like a
            regular matplotlib.figure object.

        ax1: Matplotlib axes
            The main axes of the figure. This attribute will always contain a matplotlib.axes
            instance, regardless of how the plot (which, grouping, mode attributes) is set up.

        ax2: Matplotlib axes || (default: None)
            This attribute will only contain a matplotlib.axes instance when plotting the phase
            field and order parameter separately (i.e. when which='both', grouping='separate').

            Both the ax1 and ax2 attributes can be manipulated like all other Matplotlib axes
            instances.

        colormap: str, Matplotlib color map || (default: 'twilight')
            Determines the color map for the phase field contour plot and order parameter markers
            where relevant. Can either be given as a Matplotlib color map name (str) or as a
            Matplotlib color map object.

        pf_transparency: float || (default: 1.0)
            Phase field contour plot transparency.

            This can be set either by using this parameter or by using the set_pf_transparency
            method as described below.

        marker_density_x: float || (default: 0.1)
            Determines the density of markers along x-direction as a fraction of the number of
            points in the x-coordinate.
        
        marker_density_y: float || (default: 0.1)
            Determines the density of markers along y-direction as a fraction of the number of
            points in the y-coordinate.

        marker_type: str || 'patch' | 'point' | 'tick' | 'patch & point' | 'patch & tick' | 'point & tick' | 'all' | (default: 'all')
            Sets the order parameter marker type.
            'patch' - regular polygon of order p for p >= 3. For p < 3, the marker becomes
                      a point that is not visible in the plot,
            'point' - regular asterisk of order p for p >= 3. For p = 2, the marker becomes
                      a straight line, as is appropriate for a nematic,
             'tick' - a single dash used to mark where the phase field is considered to be
                      zero,
              other - the other allowed values for the marker_type attribute result in some
                      combination of the three basic marker types described above.
            The marker type can be set either by using this attribute or by using the
            set_marker_type method as described below.

        marker_size: int, float || (default: 500)
            The size of the order parameter markers. This parameter determines the size for all
            three of the basic marker types. There is no way to change their sizes individually.

            The marker size can be set either by using this attribute or by using the
            set_marker_size method as described below.

        marker_colors: dict{'marker_name':Matplotlib color} || (default: 'patch':'k', 'point':'k', 'tick':'r')
            Contains the colors for the three basic order parameter markers.

            The marker color can be set either by using this attribute or by using the
            set_marker_color method as described below. The values that are accepted for the color
            are same as those accepted by Matplotlib.

        marker_linewidths: dict{'marker_name':float} || (default: 'patch':0, 'point':0.2, 'tick':0.5)
            Contains the linewidth values for each of the three basic order parameter markers.

            The marker linewidths can either be set using this attribute or by using the
            set_marker_linewidth method as described below.

        marker_transparencies: dict{'marker_name':float} || (default: 'patch':0.5, 'point':1.0, 'tick':1.0)
            Contains the transparency values each of the three basic markers.

            The marker transparency values can be set either by using this attribute or by using
            the set_marker_transparency method as described below.

    Class Methods
        set_grid(c,which='both')
            Sets up the coordinate grid(s) for the plot. If this method is called before the user
            supplies any phase field data, then only the limits of the coordinate intervals will be
            extracted from the input while the rest of the data is discarded. The full grid will then
            be constructed automatically from the limits once the user supplies the phase field array.

            Positional arguments:
                c: tuple, list, array
                    c can be given as a tuple or list with two elements defining the range(s) for the
                    given coordinate axis.

                    Alternatively, c can also be given as a 1D or 2D numpy array, in which case the
                    coordinate grid will be constructed directly from these.

            Keyword argumets:
                which: str || 'x' | 'y' | 'both' | (default: 'both')
                    Determines which of the coordinate axes the given input is for.

                       'x' - sets the x-coordinate grid,
                       'y' - sets the y-coordinate grid,
                    'both' - sets the same coordinate grid for both the x- and y-axes.

        set_phi(data)
            Sets the phase field data. If there are any pre-existing coordinate limits in the animator
            object, then supplying the phase field data will automatically construct the corresponding
            coordinate grid(s) from these limits. Otherwise, the method will construct a default grid
            on the unit square [0,1]x[0,1].

            This method can also be used to completely change a pre-existing phase field array to a new
            one. In that case, the new phase field array doesn't need to be of the exact same shape as
            the old one (although its shape must still be of the form (nt,ny,nx)). The coordinate grids
            will automatically be adjusted to match the shape of the phase field array along the last
            two axes.

            Positional arguments:
                data: array
                    The phase field data must be given as a 3D array with shape (nt,ny,nx).

        set_which(which)
            Determines whether to plot the phase field, order parameter or both.

            The default setting for which is 'pf'.

            Positional arguments:
                which: str || 'pf', 'op', 'both'
                      'pf' - phase field,
                      'op' - order parameter,
                    'both' - phase field and order parameter.

        set_grouping(grouping)
            Determines how to group the phase field and order parameter plots. This method only has
            effect if the which='both' (see also the main class doc string). Otherwise the grouping
            parameter is ignored.

            The default setting for grouping is 'together'.

            Positional arguments:
                grouping: str || 'separate', 'together'
                    'separate' - plot the phase field and order parameter in each their own coordinate
                                 system,
                    'together' - plot the phase field and order parameter in the same coordinate
                                 system.

        set_mode(mode)
            Sets the plotting mode when plotting both the phase field and order parameter (i.e. when
            which='both'). This method only has effect if the grouping is set to 'together'.
            Otherwise the mode parameter is ignored.

            If the mode is changed to 1 or 2 (with which='both' and grouping='together'), then this
            method will automatically change the marker type to the default for those two modes, and
            will override the set_marker_type method if it is called before set_mode. However, the
            marker type can still be changed by changed by calling set_marker_type after changing the
            mode. The same goes for the marker transparencies.

            Likewise for the patch marker color - changing the mode to 1 or 2 will automatically set
            the patch marker color to the phase field color map with no possibility of changing this
            (the point and tick colors can still be changed as desired, though this must also be done
            after calling set_mode in order to have any effect).

            The default setting for mode is 0.

            Positional arguments:
                mode: int || 0, 1, 2
                    0 - plot the order parameter with solid colored markers over phase field,
                    1 - plot the order parameter with the phase field values color mapped to each
                        marker,
                    2 - plot the order parameter with the phase field values color mapped to each
                        marker over semi-transparent phase field.

        set_marker_density(density,direction='both')
            Sets the density of markers along either x- or y-axis, or both simultaneously. If called
            without a defined coordinate grid in the specified direction, then the method will have
            no effect.

            Positional arguments:
                density: int, float || (0,1]
                    Determines the marker density along the direction specified by the direction
                    keyword argument.

            Keyword arguments:
                direction: str || (default: 'both')
                    Specifies the direction along which the given density should apply.

                    If the direction is set to 'both' without a fully defined coordinate grid, then the
                    marker density will be set only for the direction for which the coordinate grid is
                    defined.

        reset_marker_settings()
            Resets the marker type, color, transparency, size and linewidths to the default values for
            any given plotting configuration.

        set_marker_type(marker_type)
            Sets the marker type for the order parameter markers.

            If the plotting mode is changed to 1 or 2 (with which='both' and grouping='together')
            from any of the other plotting configurations, then this method will have no effect on the
            marker type if it is called before set_mode, since set_mode sets a default marker type for
            the modes 1 and 2 (see also the set_mode doc string).

            Positional arguments:
                marker_type: str || 'patch', 'point', 'tick', 'patch & point', 'patch & tick', 'point & tick', 'all'
                    'patch' - regular polygon of degree p for p >= 3. p < 3 gives just a point which is
                              not visible in the final plot,
                    'point' - regular asterisk of degree p for p >= 3. For p = 2, the marker just
                              becomes a line, as is appropriate for a nematic,
                     'tick' - single dash used to mark where the phase field is considered to be zero
                      other - all the other allowed values for the marker_type set any combination of
                              the three basic marker sub-types.

        set_marker_color(color,which="patch")
            Sets the color for any of the three marker sub-types.

            This method will have no effect on the patch color in the modes 1 and 2 (with which='both'
            and grouping='together') as the patch color will be set to the phase field color map in
            those modes.

            Positional arguments:
                color: any Matplotlib-compatible color

            Keyword arguments:
                which: str || 'patch' | 'point' | 'tick' | (default: 'patch')
                    Determines which of the marker sub-types the color should apply to.

        set_marker_size(size)
            Sets the size of the order parameter markers. The same size is set for all three of the
            marker sub-types at once with no option of affecting each one individually.

            By default, the marker sizes are set automatically based on the marker density, but this
            can be overwritten using this method.

            Positional arguments:
                size: float, int
                    Sets the marker size.

        set_marker_linewidth(linewidth,which="point")
            Sets the linewidth for any of the three basic marker sub-types.

            If p = 1,2, then by default the marker linewidtsh will be set automatically based on the
            marker density, but this can be overwritten using this method.

            Positional arguments:
                linewidth: float

            Keyword arguments:
                which: str || 'patch' | 'point' | 'tick' | (default: 'point')
                    Determines which of the basic marker sub-types the linewidth should apply to.

        set_marker_transparency(alpha,which="patch")
            Sets the transparency for any of the three basic marker sub-types. The effects of this
            method will be overwritten by the set_mode method if the mode is changed to 1 or 2 (with
            which='both' and grouping='together') from any other plotting configuration. The
            transparency can be set to any desired value by calling this method after set_mode
            (see also the set_mode doc string).

            Positional arguments:
                alpha: float
                    Transparency value. Because the transparency must be a number in the interval
                    [0,1], if alpha is greater than 1, the transparency will be set to 1.

            Keyword arguments:
                which: str || 'patch' | 'point' | 'tick' | (default: 'patch')
                    Determines which of the marker sub-types the transparency should apply to.

        set_colormap(colormap)
            Sets the color map for the phase field contour plot and order parameter markers where
            relevant.

            Positional arguments:
                colormap: str, Matplotlib colormap
                    The colormap can be given as a string with the name of any of the standard
                    Matplotlib colormaps, or as a Matplotlib colormap object.

        set_pf_transparency(alpha)
            Sets the transparency of the phase field contour plot. Calling this before set_mode will
            have no effect on the phase field contour plot transparency, as the set_mode method sets
            a default value for the transparency. However, calling the method after set_mode will set
            the transparency to the desired value.

            Positional arguments:
                alpha: float
                    Transparency value. Because the transparency must be a number in the interval
                    [0,1], if alpha is greater than 1, the phase field transparency will be set to 1.

        preview(frame=None)
            Allows the user to preview a single frame of the animation.

            Keyword arguments:
                frame: int || (default: None)
                    Determines which frame of the animation to preview. If frame > nt, it will simply
                    be set to nt-1.

        animate(ext='gif')
            Makes the animation of the phase field/ order parameter time evolution and saves it to the
            same location as the script from which the method is called.

            Keyword arguments:
                ext: str || 'gif' | 'mp4 | (default: 'gif')
                    Sets the output file type for the animation.
    '''

    _marker_types = ("patch","point","tick","patch & point","patch & tick","point & tick","all")
    _which_list = ["pf","op","both"]
    _grouping_list = ["separate","together"]
    _mode_list = [0,1,2]

    def __init__(self,p,field=None,x=None,y=None):
        '''
        Initializes an instance of the PaticAnimator class based on the supplied parameters.

        Positional arguments:
            p: int
                The degree of the p-atic the object will be animating. The value of p is used to
                determine the proper marker style for the p-atic of interest.

        Keyword arguments:
            field: array || (default: None)
                The phase field array. This must be a 3D array of shape (nt,ny,nx), with nt being
                the number of time steps in the evolution of the phase field, i.e. the number of
                frames for the animation, and nx and ny specifying the size of the coordinate grid.

                If field is the only keyword argument that is given, then the animator will
                automatically construct a coordinate grid on the unit square [0,1]x[0,1].

            x,y: tuple, list, array || (default: None)
                The coordinates for the grid on which to plot the phase field/ order parameter. If
                given as tuple/list, then the tuple/list will specify the end points of the
                interval along the given axis. If given as an array, it can either be a 1D or 2D
                array, the animator will construct an appropriate grid for that coordinate regard-
                less.

                If the coordinates are given without the phase field array, then only the end-
                points of the intervals will be extracted, while the rest of the data will be
                discarded. The full coordinate grid will then be constructed automatically from
                these limits once the user supplies a phase field array.

                If only one of the coordinates is given (with or without the phase field array),
                then the same interval will be used for both axes and the grid will be constructed
                accordingly.

                If both coordinates are given (with or without the phase field array), then the
                grid will be constructed as specified by the user.
        '''
        if not isinstance(p,int):
            raise TypeError("""p must be an integer.""")
        elif isinstance(p,int) and p < 1:
            raise ValueError("""p must be greater than or qual to 1.""")
        else:
            self.p = p

        self.which = "pf"
        self.grouping = "together"
        self.mode = 0

        self._markers = {"patch":(p,0,-90), "point":(p,2,-90), "tick":(1,2,-90)}
        self.marker_type = "all"
        self.marker_size = 500
        self.marker_colors = {"patch":'k', "point":'k', "tick":'r'}
        self.marker_linewidths = {"patch":0, "point":0.2, "tick":0.5}
        self.marker_transparencies = {"patch":0.5, "point":1.0, "tick":1.0}

        self.pf_transparency = 1.0
        self.colormap = "twilight"
        self.ax_fc = 'whitesmoke'

        self.fig = plt.figure(figsize=(12.0,10.0))
        self.ax1 = self.fig.add_subplot(111,facecolor=self.ax_fc)
        self.ax2 = None

        self.marker_density_x = 0.1
        self.marker_density_y = 0.1

        self._slc_x = 1
        self._slc_y = 1

        if field is None:
            self.field = None

            self.nx = None
            self.x = None

            self.ny = None
            self.y = None

            self.nt = None

            if x is None and y is None:
                self.x0 = None
                self.x1 = None

                self.y0 = None
                self.y1 = None    
            elif (x is not None and y is None) or (x is None and y is not None):
                if x is not None:
                    self._check_coordinate(x)

                    self.x0 = np.min(x)
                    self.x1 = np.max(x)

                    self.y0 = np.min(x)
                    self.y1 = np.max(x)
                elif y is not None:
                    self._check_coordinate(y)

                    self.x0 = np.min(y)
                    self.x1 = np.max(y)

                    self.y0 = np.min(y)
                    self.y1 = np.max(y)
            elif x is not None and y is not None:
                self._check_coordinate(x)
                self._check_coordinate(y)

                self.x0 = np.min(x)
                self.x1 = np.max(x)

                self.y0 = np.min(y)
                self.y1 = np.max(y)
        elif field is not None:
            self._check_phi(field)

            self.nx = field.shape[2]
            self.ny = field.shape[1]
            self.nt = field.shape[0]

            self.field = field

            self._slc_x = self.nx//int(self.marker_density_x*self.nx)
            self._slc_y = self.ny//int(self.marker_density_y*self.ny)

            if x is None and y is None:
                self._set_default_grid()
            elif (x is not None and y is None) or (x is None and y is not None):
                if x is not None:
                    self._check_coordinate(x)
                    self._set_grid_from_coordinate(x,which='both')
                elif y is not None:
                    self._check_coordinate(y)
                    self._set_grid_from_coordinate(y,which='both')
            elif x is not None and y is not None:
                self._check_coordinate(x)
                self._check_coordinate(y)
                self._set_grid_from_coordinate(x,which='x')
                self._set_grid_from_coordinate(y,which='y')

            self._set_marker_size()

    def _check_phi(self,field):
        '''
        Internal method for checking that the phase field array is of the correct type and has the
        right shape.

        Called in:
            - __init__
            - set_phi

        Calls on:
            - None
        '''
        if not isinstance(field,np.ndarray):
            raise TypeError("""field must be of type <class 'numpy.ndarray'>.""")
        elif isinstance(field,np.ndarray) and len(field.shape) != 3:
            raise Exception("""field must be a three-dimensional array with shape (nt,ny,nx).""")

        if field.dtype == np.complex_:
            self.complex_field = True
        else:
            self.complex_field = False

    def _check_coordinate(self,c):
        '''
        Internal method for checking that the coordinate inputs have the correct type and shape.

        Called in:
            - __init__
            - set_grid

        Calls on:
            - None
        '''
        if isinstance(c,tuple) or isinstance(c,list):
            if len(c) != 2:
                raise ValueError("""The coordinate limits must be given as a tuple or list of two numbers.""")

            for ci in c:
                if not (isinstance(ci,float) or isinstance(ci,int)):
                    raise ValueError("""The coordinate limits must be numbers.""")

            if c[1] <= c[0]:
                raise ValueError("""The upper coordinate limit must be greater than the lower coordinate limit.""")
        elif isinstance(c,np.ndarray):
            if len(c.shape) > 2:
                raise Exception("""The coordinate array must either be one- or two-dimensional.""")
            elif self.field is not None and len(c.shape) == 2 and c.shape != self.field.shape[1:]: # ---------------------------------------------------- CHECK IF THIS IS NECESSARY
                raise Exception("""The shape of the coordinate grid must be (ny,nx) = (field.shape[1],field.shape[2]) = %s.""" % (self.field.shape[1:],))
        else:
            raise TypeError("""The coordinate keyword arguments must be either of type <class 'tuple'>, <class 'list'> or <class 'numpy.ndarray'>.""")

    def _set_grid_from_coordinate(self,c,which=None):
        '''
        Internal method for constructing the coordinate grids from the user-supplied coordinate
        inputs.

        Called in:
            - __init__
            - set_grid
            - set_phi

        Calls on:
            - None
        '''
        if which == "x":
            self.x0 = np.min(c)
            self.x1 = np.max(c)
            self.x = np.tile(np.linspace(self.x0,self.x1,self.nx),(self.ny,1))
        elif which == "y":
            self.y0 = np.min(c)
            self.y1 = np.max(c)
            self.y = np.tile(np.linspace(self.y0,self.y1,self.ny),(self.nx,1)).T
        elif which == "both":
            self.x0 = np.min(c)
            self.x1 = np.max(c)

            self.y0 = np.min(c)
            self.y1 = np.max(c)

            self.x, self.y = np.meshgrid(np.linspace(self.x0,self.x1,self.nx),np.linspace(self.y0,self.y1,self.ny))

    def _set_default_grid(self):
        '''
        Internal method for constructing the default coordinate grid on the unit square [0,1]x[0,1]
        in the xy-plane.

        Called in:
            - __init__
            - set_phi

        Calls on:
            - None
        '''
        self.x0 = 0
        self.x1 = 1

        self.y0 = 0
        self.y1 = 1

        self.x, self.y = np.meshgrid(np.linspace(self.x0,self.x1,self.nx),np.linspace(self.y0,self.y1,self.ny))

    def _initialize_plot(self):
        '''
        Internal method for initializing the plot based on which of the phase field and order
        parameter to plot, how they're grouped and what mode they're to be displayed in.

        Called in:
            - preview
            - animate

        Calls on:
            - _set_marker
        '''
        self.ax1.set_facecolor(self.ax_fc)
        self.SM = ScalarMappable(cmap=self.colormap)

        if self.complex_field:
            self.thetas = np.angle(self.field)/self.p
            self.rs = np.abs(self.field)
            self.rs_norm = (self.rs - np.min(self.rs))/(np.max(self.rs) - np.min(self.rs))

            self.SM.set_clim([np.min(self.thetas),np.max(self.thetas)])

            self.RGBA = self.SM.to_rgba(self.thetas[0,:,:])
            self.RGBA[:,:,-1] = self.rs_norm[0,:,:]

            self.cont = self.ax1.pcolormesh(self.x,self.y,self.RGBA,shading='nearest',cmap=self.colormap,vmin=np.min(self.thetas),vmax=np.max(self.thetas),zorder=0)
            self.CB = self.fig.colorbar(self.SM,ax=self.ax1,fraction=0.07,pad=0.0175,ticks=np.linspace(np.min(self.thetas),np.max(self.thetas),9))
            self.CB.ax.set_facecolor(self.ax_fc)

            tick_labels = []
            for i in range(9):
                n = np.abs(8 - 2*i)
                d = 4*self.p

                nr = n/np.gcd(n,d)
                dr = d/np.gcd(n,d)

                if i < 4:
                    if nr == 1 and dr == 1:
                        label = r'$-\pi$'
                    elif nr == 1:
                        label = r'$-\frac{\pi}{%d}$' % dr
                    elif dr == 1:
                        label = r'$-%d\pi$' % nr
                    else:
                        label = r'$-\frac{%d\pi}{%d}$' % (nr,dr)
                elif i == 4:
                    label = r'$0$'
                else:
                    if nr == 1 and dr == 1:
                        label = r'$\pi$'
                    elif nr == 1:
                        label = r'$\frac{\pi}{%d}$' % dr
                    elif dr == 1:
                        label = r'$%d\pi$' % nr
                    else:
                        label = r'$\frac{%d\pi}{%d}$' % (nr,dr)
                tick_labels.append(label)
            self.CB.set_ticklabels(tick_labels)
        else:
            if self.p == 1:
                self._vx = np.cos((self.field/180)*np.pi)
                self._vy = np.sin((self.field/180)*np.pi)

            if self.which == "both" and self.grouping == "separate":
                self.cont = self.ax1.pcolormesh(self.x,self.y,self.field[0,:,:],shading='nearest',
                                                cmap=self.colormap,alpha=self.pf_transparency,vmin=np.min(self.field),vmax=np.max(self.field),zorder=0)
                if self.p == 1:
                    self.arrow = self.ax2.quiver(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],self._vx[0,::self._slc_y,::self._slc_x],self._vy[0,::self._slc_y,::self._slc_x],
                                                 color='k',
                                                 pivot='mid',
                                                 width=0.0025,headwidth=2.5,headlength=5,headaxislength=4.5,
                                                 scale_units='xy',scale=None,zorder=1)
                else:
                    self.patch = self.ax2.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                  marker=self._markers["patch"],
                                                  s=self.marker_size,
                                                  c=self.marker_colors["patch"],
                                                  alpha=self.marker_transparencies["patch"],
                                                  linewidths=self.marker_linewidths["patch"],
                                                  zorder=1)
                    self.point = self.ax2.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                  marker=self._markers["point"],
                                                  s=self.marker_size,
                                                  c=self.marker_colors["point"],
                                                  alpha=self.marker_transparencies["point"],
                                                  linewidths=self.marker_linewidths["point"],
                                                  zorder=2)
                    self.tick = self.ax2.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                 marker=self._markers["tick"],
                                                 s=self.marker_size,
                                                 c=self.marker_colors["tick"],
                                                 alpha=self.marker_transparencies["tick"],
                                                 linewidths=self.marker_linewidths["tick"],
                                                 zorder=3)

                    self._set_marker()

                self.ax2.set_xlim([self.x0,self.x1])
                self.ax2.set_ylim([self.y0,self.y1])
            else:
                if self.which == "pf":
                    self.cont = self.ax1.pcolormesh(self.x,self.y,self.field[0,:,:],shading='nearest',
                                                    cmap=self.colormap,alpha=self.pf_transparency,vmin=np.min(self.field),vmax=np.max(self.field),zorder=0)
                elif self.which == "op":
                    self.fig.set_figheight(10.0)
                    self.fig.set_figwidth(10.0)

                    if self.p == 1:
                        self.arrow = self.ax1.quiver(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],self._vx[0,::self._slc_y,::self._slc_x],self._vy[0,::self._slc_y,::self._slc_x],
                                                     color='k',
                                                     pivot='mid',
                                                     width=0.0025,headwidth=2.5,headlength=5,headaxislength=4.5,
                                                     scale_units='xy',scale=None,zorder=1)
                    else:
                        self.patch = self.ax1.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                      marker=self._markers["patch"],
                                                      s=self.marker_size,
                                                      c=self.marker_colors["patch"],
                                                      alpha=self.marker_transparencies["patch"],
                                                      linewidths=self.marker_linewidths["patch"],
                                                      zorder=1)
                        self.point = self.ax1.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                      marker=self._markers["point"],
                                                      s=self.marker_size,
                                                      c=self.marker_colors["point"],
                                                      alpha=self.marker_transparencies["point"],
                                                      linewidths=self.marker_linewidths["point"],
                                                      zorder=2)
                        self.tick = self.ax1.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                     marker=self._markers["tick"],
                                                     s=self.marker_size,c=self.marker_colors["tick"],
                                                     alpha=self.marker_transparencies["tick"],
                                                     linewidths=self.marker_linewidths["tick"],
                                                     zorder=3)

                        self._set_marker()
                elif self.which == "both":
                    if self.mode == 0:
                        self.cont = self.ax1.pcolormesh(self.x,self.y,self.field[0,:,:],shading='nearest',
                                                        cmap=self.colormap,alpha=self.pf_transparency,vmin=np.min(self.field),vmax=np.max(self.field),zorder=0)
                        if self.p == 1:
                            self.arrow = self.ax1.quiver(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],self._vx[0,::self._slc_y,::self._slc_x],self._vy[0,::self._slc_y,::self._slc_x],
                                                         color='k',
                                                         pivot='mid',
                                                         width=0.0025,headwidth=2.5,headlength=5,headaxislength=4.5,
                                                         scale_units='xy',scale=None,zorder=1)
                        else:
                            point_kwarg = {"c":self.marker_colors["point"]}
                            patch_kwarg = {"c":self.marker_colors["patch"]}
                    elif self.mode == 1:
                        if self.p == 1:
                            self.arrow = self.ax1.quiver(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],self._vx[0,::self._slc_y,::self._slc_x],self._vy[0,::self._slc_y,::self._slc_x],self.field[0,::self._slc_y,::self._slc_x],
                                                         cmap=self.colormap,
                                                         pivot='mid',
                                                         width=0.0025,headwidth=2.5,headlength=5,headaxislength=4.5,
                                                         scale_units='xy',scale=None,zorder=1)
                        elif self.p == 2:
                            point_kwarg = {"c":self.field[0,::self._slc_y,::self._slc_x],"cmap":self.colormap}
                        else:
                            point_kwarg = {"c":self.marker_colors["point"]}
                        patch_kwarg = {"c":self.field[0,::self._slc_y,::self._slc_x],"cmap":self.colormap,"vmin":np.min(self.field[0,:,:]),"vmax":np.max(self.field[0,:,:])}
                    elif self.mode == 2:
                        self.cont = self.ax1.pcolormesh(self.x,self.y,self.field[0,:,:],shading='nearest',
                                                        cmap=self.colormap,alpha=self.pf_transparency,vmin=np.min(self.field),vmax=np.max(self.field),zorder=0)
                        if self.p == 1:
                            self.arrow = self.ax1.quiver(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],self._vx[0,::self._slc_y,::self._slc_x],self._vy[0,::self._slc_y,::self._slc_x],self.field[0,::self._slc_y,::self._slc_x],
                                                         cmap=self.colormap,
                                                         pivot='mid',
                                                         width=0.0025,headwidth=2.5,headlength=5,headaxislength=4.5,
                                                         scale_units='xy',scale=None,zorder=1)
                        elif self.p == 2:
                            point_kwarg = {"c":self.field[0,::self._slc_y,::self._slc_x],"cmap":self.colormap}
                        else:
                            point_kwarg = {"c":self.marker_colors["point"]}
                        patch_kwarg = {"c":self.field[0,::self._slc_y,::self._slc_x],"cmap":self.colormap,"vmin":np.min(self.field[0,:,:]),"vmax":np.max(self.field[0,:,:])}

                    if self.p > 1:
                        self.patch = self.ax1.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                      marker=self._markers["patch"],
                                                      s=self.marker_size,
                                                      alpha=self.marker_transparencies["patch"],
                                                      linewidths=self.marker_linewidths["patch"],
                                                      zorder=1,
                                                      **patch_kwarg)
                        self.point = self.ax1.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                      marker=self._markers["point"],
                                                      s=self.marker_size,
                                                      alpha=self.marker_transparencies["point"],
                                                      linewidths=self.marker_linewidths["point"],
                                                      zorder=2,
                                                      **point_kwarg)
                        self.tick = self.ax1.scatter(self.x[::self._slc_y,::self._slc_x],self.y[::self._slc_y,::self._slc_x],
                                                     marker=self._markers["tick"],
                                                     s=self.marker_size,
                                                     c=self.marker_colors["tick"],
                                                     alpha=self.marker_transparencies["tick"],
                                                     linewidths=self.marker_linewidths["tick"],
                                                     zorder=3)

                        self._set_marker()

            self.ax1.set_xlim([self.x0,self.x1])
            self.ax1.set_ylim([self.y0,self.y1])

            if self.which != 'op':
                if self.p == 1 and self.grouping == 'together' and self.mode == 1:
                    self.SM.set_clim([np.min(self.field),np.max(self.field)])
                    self.CB = self.fig.colorbar(self.SM,ax=self.ax1,fraction=0.07,pad=0.0175,ticks=np.linspace(np.min(self.field),np.max(self.field),9))
                    self.CB.ax.set_facecolor(self.ax_fc)
                else:
                    self.cont.set_clim([np.min(self.field),np.max(self.field)])
                    self.CB = self.fig.colorbar(self.cont,ax=self.ax1,fraction=0.07,pad=0.0175,ticks=np.linspace(np.min(self.field),np.max(self.field),9))
                    self.CB.ax.set_facecolor(self.ax_fc)

        self.fig.tight_layout()

    def _set_marker_size(self):
        '''
        Internal method for setting the marker size (p >= 3) or linewidths (p = 1,2) based on the
        number of markers along the axis with the biggest number of points.

        Called in:
            - __init__
            - set_phi
            - set_marker_density
            - reset_marker_settings

        Calls on:
            - None
        '''
        nmax = np.max([self.nx,self.ny])
        N = int(self.marker_density_x*nmax) if self.nx >= self.ny else int(self.marker_density_y*nmax)

        if N >= 10 and N <= 60:
            if N >= 10 and N < 20:
                if self.p >= 3:
                    self.marker_size = 140
                else:
                    self.marker_linewidths["point"] = 1.75
                    self.marker_linewidths["tick"] = 1.75

                    self.marker_size = 140
            elif N >= 20 and N < 30:
                if self.p >= 3:
                    self.marker_size = 100
                else:
                    self.marker_linewidths["point"] = 1.0
                    self.marker_linewidths["tick"] = 1.0

                    self.marker_size = 140
            elif N >= 30 and N < 40:
                if self.p >= 3:
                    self.marker_size = 60
                else:
                    self.marker_linewidths["point"] = 0.85
                    self.marker_linewidths["tick"] = 0.85

                    self.marker_size = 60
            elif N >= 40 and N < 50:
                if self.p >= 3:
                    self.marker_size = 30
                else:
                    self.marker_linewidths["point"] = 0.85
                    self.marker_linewidths["tick"] = 0.85

                    self.marker_size = 45
            elif N >= 50 and N <= 60:
                if self.p >= 3:
                    self.marker_size = 20
                else:
                    self.marker_linewidths["point"] = 0.85
                    self.marker_linewidths["tick"] = 0.85

                    self.marker_size = 30
        elif N < 10:
            N = 10
            if self.p >= 3:
                self.marker_size = 140
            else:
                self.marker_linewidths["point"] = 1.75
                self.marker_linewidths["tick"] = 1.75

                self.marker_size = 140
        elif N > 60:
            if self.p >= 3:
                self.marker_size = 20
            else:
                self.marker_linewidths["point"] = 0.85
                self.marker_linewidths["tick"] = 0.85

                self.marker_size = 30

    def _set_marker(self):
        '''
        Internal method for displaying the right marker type based on the marker_type attribute.

        Called in:
            - _initialize_plot

        Calls on:
            - None
        '''
        if self.marker_type == "patch":
            self.point.remove()
            self.tick.remove()
        elif self.marker_type == "point":
            self.patch.remove()
            self.tick.remove()
        elif self.marker_type == "tick":
            self.patch.remove()
            self.point.remove()
        elif self.marker_type == "patch & point":
            self.tick.remove()
        elif self.marker_type == "patch & tick":
            self.point.remove()
        elif self.marker_type == "point & tick":
            self.patch.remove()
        elif self.marker_type == "all":
            pass

    def _update_markers(self,patch_markers,point_markers,tick_markers):
        '''
        Internal method for setting the correct markers for every value of the phase field at a
        given time step based on the inputs from the _init_frame and _draw_frame methods.

        Called in:
            - _init_frame
            - _draw_frame

        Calls on:
            - None
        '''
        patch_paths = []
        point_paths = []
        tick_paths = []

        for patch_marker,point_marker,tick_marker in zip(patch_markers,point_markers,tick_markers):
            if isinstance(patch_marker, mmarkers.MarkerStyle):
                patch_marker_obj = patch_marker
            else:
                patch_marker_obj = mmarkers.MarkerStyle(patch_marker)

            if isinstance(point_marker, mmarkers.MarkerStyle):
                point_marker_obj = point_marker
            else:
                point_marker_obj = mmarkers.MarkerStyle(point_marker)

            if isinstance(tick_marker, mmarkers.MarkerStyle):
                tick_marker_obj = tick_marker
            else:
                tick_marker_obj = mmarkers.MarkerStyle(tick_marker)

            patch_path = patch_marker_obj.get_path()#.transformed(patch_marker_obj.get_transform())
            patch_paths.append(patch_path)

            point_path = point_marker_obj.get_path()#.transformed(point_marker_obj.get_transform())
            point_paths.append(point_path)

            tick_path = tick_marker_obj.get_path()#.transformed(tick_marker_obj.get_transform())
            tick_paths.append(tick_path)

        if self.marker_type == "patch":
            self.patch.set_paths(patch_paths)
        elif self.marker_type == "point":
            self.point.set_paths(point_paths)
        elif self.marker_type == "tick":
            self.tick.set_paths(tick_paths)
        elif self.marker_type == "patch & point":
            self.patch.set_paths(patch_paths)
            self.point.set_paths(point_paths)
        elif self.marker_type == "patch & tick":
            self.patch.set_paths(patch_paths)
            self.tick.set_paths(tick_paths)
        elif self.marker_type == "point & tick":
            self.point.set_paths(point_paths)
            self.tick.set_paths(tick_paths)
        elif self.marker_type == "all":
            self.patch.set_paths(patch_paths)
            self.point.set_paths(point_paths)
            self.tick.set_paths(tick_paths)

    def _draw_frame(self,i):
        '''
        Internal method for drawing every frame of the animation by updating the phase field and/
        or order parameter markers based on the phase field value at time step i.

        This method is also used in the preview method for previewing any particular frame of the
        animation if the user should want to do so.

        Called in:
            - preview
            - animate

        Calls on:
            - _update_markers
        '''
        if self.complex_field:
            self.CB.remove()
            self.cont.remove()

            GS = mgs.GridSpec(1,1,figure=self.fig)
            self.ax1.set_subplotspec(GS[0])

            self.RGBA = self.SM.to_rgba(self.thetas[i,:,:])
            self.RGBA[:,:,-1] = self.rs_norm[i,:,:]

            self.cont = self.ax1.pcolormesh(self.x,self.y,self.RGBA,shading='nearest',cmap=self.colormap,vmin=np.min(self.thetas),vmax=np.max(self.thetas),zorder=0)
            self.CB = self.fig.colorbar(self.SM,ax=self.ax1,fraction=0.07,pad=0.0175,ticks=np.linspace(np.min(self.thetas),np.max(self.thetas),9))
            self.CB.ax.set_facecolor(self.ax_fc)

            tick_labels = []
            for i in range(9):
                n = np.abs(8 - 2*i)
                d = 4*self.p

                nr = n/np.gcd(n,d)
                dr = d/np.gcd(n,d)

                if i < 4:
                    if nr == 1 and dr == 1:
                        label = r'$-\pi$'
                    elif nr == 1:
                        label = r'$-\frac{\pi}{%d}$' % dr
                    elif dr == 1:
                        label = r'$-%d\pi$' % nr
                    else:
                        label = r'$-\frac{%d\pi}{%d}$' % (nr,dr)
                elif i == 4:
                    label = r'$0$'
                else:
                    if nr == 1 and dr == 1:
                        label = r'$\pi$'
                    elif nr == 1:
                        label = r'$\frac{\pi}{%d}$' % dr
                    elif dr == 1:
                        label = r'$%d\pi$' % nr
                    else:
                        label = r'$\frac{%d\pi}{%d}$' % (nr,dr)
                tick_labels.append(label)
            self.CB.set_ticklabels(tick_labels)
        else:
            if self.which == "pf":
                self.CB.remove()
                self.cont.remove()
                self.cont = self.ax1.pcolormesh(self.x,self.y,self.field[i,:,:],shading='nearest',
                                                cmap=self.colormap,alpha=self.pf_transparency,vmin=np.min(self.field),vmax=np.max(self.field),zorder=0)
                self.cont.set_clim([np.min(self.field),np.max(self.field)])
                self.CB = self.fig.colorbar(self.cont,ax=self.ax1,fraction=0.07,pad=0.0175,ticks=np.linspace(np.min(self.field),np.max(self.field),9))
                self.CB.ax.set_facecolor(self.ax_fc)
            else:
                if self.p == 1:
                    self.arrow.set_UVC(self._vx[i,::self._slc_y,::self._slc_x],self._vy[i,::self._slc_y,::self._slc_x])
                elif self.p > 1:
                    patch_markers = []
                    point_markers = []
                    tick_markers = []

                    for j in range(0,len(self.field[i,:,:]),self._slc_y):
                        for k in range(0,len(self.field[i,j,:]),self._slc_x):
                            t = Affine2D().rotate_deg(self.field[i,j,k]-90)
                            patch_markers.append(mpath.Path.unit_regular_polygon(self.p).transformed(t))
                            point_markers.append(mpath.Path.unit_regular_asterisk(self.p).transformed(t))
                            tick_markers.append(mpath.Path.unit_regular_asterisk(1).transformed(t))

                    self._update_markers(patch_markers,point_markers,tick_markers)

                if self.which == "both" and self.grouping == "together":
                    if self.mode == 0:
                        self.CB.remove()
                        self.cont.remove()
                        self.cont = self.ax1.pcolormesh(self.x,self.y,self.field[i,:,:],shading='nearest',
                                                        cmap=self.colormap,alpha=self.pf_transparency,vmin=np.min(self.field),vmax=np.max(self.field),zorder=0)
                        self.cont.set_clim([np.min(self.field),np.max(self.field)])
                        self.CB = self.fig.colorbar(self.cont,ax=self.ax1,fraction=0.07,pad=0.0175,ticks=np.linspace(np.min(self.field),np.max(self.field),9))
                        self.CB.ax.set_facecolor(self.ax_fc)
                    elif self.mode == 1:
                        if self.p == 1:
                            self.arrow.set_array(self.field[i,::self._slc_y,::self._slc_x].ravel())
                        elif self.p == 2:
                            self.point.set_array(self.field[i,::self._slc_y,::self._slc_x].ravel())
                        else:
                            self.patch.set_array(self.field[i,::self._slc_y,::self._slc_x].ravel())
                    elif self.mode == 2:
                        self.CB.remove()
                        self.cont.remove()
                        self.cont = self.ax1.pcolormesh(self.x,self.y,self.field[i,:,:],shading='nearest',
                                                        cmap=self.colormap,alpha=self.pf_transparency,vmin=np.min(self.field),vmax=np.max(self.field),zorder=0)
                        self.cont.set_clim([np.min(self.field),np.max(self.field)])
                        self.CB = self.fig.colorbar(self.cont,ax=self.ax1,fraction=0.07,pad=0.0175,ticks=np.linspace(np.min(self.field),np.max(self.field),9))
                        self.CB.ax.set_facecolor(self.ax_fc)
                        if self.p == 1:
                            self.arrow.set_array(self.field[i,::self._slc_y,::self._slc_x].ravel())
                        elif self.p == 2:
                            self.point.set_array(self.field[i,::self._slc_y,::self._slc_x].ravel())
                        else:
                            self.patch.set_array(self.field[i,::self._slc_y,::self._slc_x].ravel())
                elif self.which == "both" and self.grouping == "separate":
                    self.CB.remove()
                    self.cont.remove()
                    self.cont = self.ax1.pcolormesh(self.x,self.y,self.field[i,:,:],shading='nearest',
                                                    cmap=self.colormap,alpha=self.pf_transparency,vmin=np.min(self.field),vmax=np.max(self.field),zorder=0)
                    self.cont.set_clim([np.min(self.field),np.max(self.field)])
                    self.CB = self.fig.colorbar(self.cont,ax=self.ax1,fraction=0.07,pad=0.0175,ticks=np.linspace(np.min(self.field),np.max(self.field),9))
                    self.CB.ax.set_facecolor(self.ax_fc)

    def set_grid(self,c,which='both'):
        '''
        Sets up the coordinate grid(s) for the plot. If this method is called before the user
        supplies any phase field data, then only the limits of the coordinate intervals will be
        extracted from the input while the rest of the data is discarded. The full grid will then
        be constructed automatically from the limits once the user supplies the phase field array.

        Positional arguments:
            c: tuple, list, array
                c can be given as a tuple or list with two elements defining the range(s) for the
                given coordinate axis.

                Alternatively, c can also be given as a 1D or 2D numpy array, in which case the
                coordinate grid will be constructed directly from these.

        Keyword argumets:
            which: str || 'x' | 'y' | 'both' | (default: 'both')
                Determines which of the coordinate axes the given input is for.

                   'x' - sets the x-coordinate grid,
                   'y' - sets the y-coordinate grid,
                'both' - sets the same coordinate grid for both the x- and y-axes.
        '''
        if which.lower() not in ["x","y","both"]:
            raise ValueError("""which must be either 'x', 'y' or 'both'.""")
        else:
            self._check_coordinate(c)
            if which == "x":
                self.x0 = np.min(c)
                self.x1 = np.max(c)
                if self.field is not None:
                    self._set_grid_from_coordinate([self.x0,self.x1],which='x')
            elif which == "y":
                self.y0 = np.min(c)
                self.y1 = np.max(c)
                if self.field is not None:
                    self._set_grid_from_coordinate([self.y0,self.y1],which='y')
            elif which == "both":
                self.x0 = np.min(c)
                self.x1 = np.max(c)
                self.y0 = np.min(c)
                self.y1 = np.max(c)
                if self.field is not None:
                    self._set_grid_from_coordinate(c,which='both')

    def set_phi(self,data):
        '''
        Sets the phase field data. If there are any pre-existing coordinate limits in the animator
        object, then supplying the phase field data will automatically construct the corresponding
        coordinate grid(s) from these limits. Otherwise, the method will construct a default grid
        on the unit square [0,1]x[0,1].

        This method can also be used to completely change a pre-existing phase field array to a new
        one. In that case, the new phase field array doesn't need to be of the exact same shape as
        the old one (although its shape must still be of the form (nt,ny,nx)). The coordinate grids
        will automatically be adjusted to match the shape of the phase field array along the last
        two axes.

        Positional arguments:
            data: array
                The phase field data must be given as a 3D array with shape (nt,ny,nx).
        '''
        self._check_phi(data)
        self.field = data
        self.nx = data.shape[2]
        self.ny = data.shape[1]
        self.nt = data.shape[0]

        self._slc_x = self.nx//int(self.marker_density_x*self.nx)
        self._slc_y = self.ny//int(self.marker_density_y*self.ny)

        if self.x is None and self.y is None:
            if self.x0 is None and self.x1 is None and self.y0 is None and self.y1 is None:
                self._set_default_grid()

                self._set_marker_size()
            elif self.x0 is not None and self.x1 is not None and self.y0 is None and self.y1 is None:
                self._set_grid_from_coordinate([self.x0,self.x1],which='x')
            elif self.x0 is None and self.x1 is None and self.y0 is not None and self.y1 is not None:
                self._set_grid_from_coordinate([self.y0,self.y1],which='y')
            elif self.x0 is not None and self.x1 is not None and self.y0 is not None and self.y1 is not None:
                self._set_grid_from_coordinate([self.x0,self.x1],which='x')
                self._set_grid_from_coordinate([self.y0,self.y1],which='y')

                self._set_marker_size()
        elif self.x is not None and self.y is None:
            if self.y0 is not None and self.y1 is not None:
                self._set_grid_from_coordinate([self.y0,self.y1],which='y')

                self._set_marker_size()
        elif self.x is None and self.y is not None:
            if self.x0 is not None and self.x1 is not None:
                self._set_grid_from_coordinate([self.x0,self.x1],which='x')

                self._set_marker_size()
        elif self.x is not None and self.y is not None:
            self._set_grid_from_coordinate([self.x0,self.x1],which='x')
            self._set_grid_from_coordinate([self.y0,self.y1],which='y')

            self._set_marker_size()

    def set_which(self,which):
        '''
        Determines whether to plot the phase field, order parameter or both.

        The default setting for which is 'pf'.

        Positional arguments:
            which: str || 'pf', 'op', 'both'
                  'pf' - phase field,
                  'op' - order parameter,
                'both' - phase field and order parameter.
        '''
        if which.lower() not in self._which_list:
            msg = """which must be one of """ + "'%s', "*(len(self._which_list)-1) + "and '%s'."
            raise ValueError(msg % tuple(self._which_list))

        try:
            self.ax2.remove()
            self.ax1.remove()
            self.fig.set_figheight(10.0)
            self.fig.set_figwidth(10.0)
            self.ax1 = self.fig.add_subplot(111,facecolor='whitesmoke')
            self.grouping = "together"
        except:
            pass

        if self.which == "pf":
            self.pf_transparency = 1.0

        self.which = which.lower()

    def set_grouping(self,grouping):
        '''
        Determines how to group the phase field and order parameter plots. This method only has
        effect if the which='both' (see also the main class doc string). Otherwise the grouping
        parameter is ignored.

        The default setting for grouping is 'together'.

        Positional arguments:
            grouping: str || 'separate', 'together'
                'separate' - plot the phase field and order parameter in each their own coordinate
                             system,
                'together' - plot the phase field and order parameter in the same coordinate
                             system.
        '''
        if grouping.lower() not in self._grouping_list:
            msg = """grouping must be one of """ + "'%s', "*(len(self._grouping_list)-1) + "and '%s'."
            raise ValueError(msg % self._grouping_list)

        if not self.complex_field:
            if self.which == "both":
                if self.grouping != grouping.lower() and grouping.lower() == "separate":
                    self.ax1.remove()
                    self.fig.set_figwidth(24.0)
                    self.fig.set_figheight(10.0)
                    self.ax1 = self.fig.add_subplot(121,facecolor=self.ax_fc)
                    self.ax2 = self.fig.add_subplot(122,facecolor='whitesmoke')
                elif self.grouping != grouping.lower() and grouping.lower() == "together":
                    self.ax1.remove()
                    self.ax2.remove()
                    self.fig.set_figwidth(12.0)
                    self.fig.set_figheight(10.0)
                    self.ax1 = self.fig.add_subplot(111,facecolor=self.ax_fc)

                if grouping.lower() == "together" and (self.mode == 1 or self.mode == 2):
                    if self.p == 2:
                        self.marker_type = "point"
                    else:
                        self.marker_type = "patch"
                        self.marker_transparencies["patch"] = 1.0
                    self.pf_transparency = 0.25
                elif grouping.lower() == "separate":
                    self.marker_type = "all"
                    self.marker_transparencies["patch"] = 0.5
                    self.pf_transparency = 1.0

        self.grouping = grouping.lower()

    def set_mode(self,mode):
        '''
        Sets the plotting mode when plotting both the phase field and order parameter (i.e. when
        which='both'). This method only has effect if the grouping is set to 'together'.
        Otherwise the mode parameter is ignored.

        If the mode is changed to 1 or 2 (with which='both' and grouping='together'), then this
        method will automatically change the marker type to the default for those two modes, and
        will override the set_marker_type method if it is called before set_mode. However, the
        marker type can still be changed by changed by calling set_marker_type after changing the
        mode. The same goes for the marker transparencies.

        Likewise for the patch marker color - changing the mode to 1 or 2 will automatically set
        the patch marker color to the phase field color map with no possibility of changing this
        (the point and tick colors can still be changed as desired, though this must also be done
        after calling set_mode in order to have any effect).

        The default setting for mode is 0.

        Positional arguments:
            mode: int || 0, 1, 2
                0 - plot the order parameter with solid colored markers over phase field,
                1 - plot the order parameter with the phase field values color mapped to each
                    marker,
                2 - plot the order parameter with the phase field values color mapped to each
                    marker over semi-transparent phase field.
        '''
        if mode not in self._mode_list:
            msg = """The allowed values for the mode keyword argument are """ + "%s, "*(len(self._mode_list)-1) + "and %s."
            raise ValueError(msg % self._mode_list)

        self.mode = mode

        if self.which == "both":
            if self.grouping == "together" and (self.mode == 1 or self.mode == 2):
                if self.p == 2:
                    self.marker_type = "point"
                else:
                    self.marker_type = "patch"
                    self.marker_transparencies["patch"] = 1.0
                self.pf_transparency = 0.25
            elif self.grouping == "separate":
                self.marker_type = "all"
                self.marker_transparencies["patch"] = 0.5
                self.pf_transparency = 1.0

    def set_marker_density(self,density,direction='both'):
        '''
        Sets the density of markers along either x- or y-axis, or both simultaneously. If called
        without a defined coordinate grid in the specified direction, then the method will have
        no effect.

        Positional arguments:
            density: int, float || (0,1]
                Determines the marker density along the direction specified by the direction
                keyword argument.

        Keyword arguments:
            direction: str || (default: 'both')
                Specifies the direction along which the given density should apply.

                If the direction is set to 'both' without a fully defined coordinate grid, then the
                marker density will be set only for the direction for which the coordinate grid is
                defined.
        '''
        if direction not in ["x","y","both"]:
            raise ValueError("""direction must be 'x', 'y' or 'both'.""")

        try:
            density = float(density)
        except:
            raise TypeError("""density must be a number in the half-open interval (0,1].""")

        if density < 0:
            raise ValueError("""density cannot be less than 0.""")
        elif density > 1:
            density = 1            

        if direction == "x":
            if self.x is not None:
                self.marker_density_x = density
                self._slc_x = self.nx//int(self.marker_density_x*self.nx)
                if self.x is not None and self.y is not None:
                    self._set_marker_size()
        elif direction == "y":
            if self.y is not None:
                self.marker_density_y = density
                self._slc_y = self.ny//int(self.marker_density_y*self.ny)
                if self.x is not None and self.y is not None:
                    self._set_marker_size()
        elif direction == "both":
            if self.x is not None and self.y is None:
                self.marker_density_x = density
                self._slc_x = self.nx//int(self.marker_density_x*self.nx)
            elif self.x is None and self.y is not None:
                self.marker_density_y = density
                self._slc_y = self.ny//int(self.marker_density_y*self.ny)
            elif self.x is not None and self.y is not None:
                self.marker_density_x = density
                self.marker_density_y = density
                self._slc_x = self.nx//int(self.marker_density_x*self.nx)
                self._slc_y = self.ny//int(self.marker_density_y*self.ny)

                self._set_marker_size()

    def reset_marker_settings(self):
        '''
        Resets the marker type, color, transparency, size and linewidths to the default values for
        any given plotting configuration.
        '''
        self._set_marker_size()

        self.marker_linewidths["patch"] = 0
        self.marker_linewidths["point"] = 0.2
        self.marker_linewidths["tick"] = 0.5

        if self.which == "op" or (self.which == "both" and self.grouping == "separate") or (self.which == "both" and self.grouping == "together" and self.mode == 0):
            self.marker_type = "all"
            self.marker_transparencies["patch"] = 0.5
            self.marker_colors["patch"] = "k"
            self.marker_colors["point"] = "k"
            self.marker_colors["tick"] = "r"
        elif self.which == "both" and (self.mode == 1 or self.mode == 2):
            self.marker_type = "patch"

    def set_marker_type(self,marker_type):
        '''
        Sets the marker type for the order parameter markers.

        If the plotting mode is changed to 1 or 2 (with which='both' and grouping='together')
        from any of the other plotting configurations, then this method will have no effect on the
        marker type if it is called before set_mode, since set_mode sets a default marker type for
        the modes 1 and 2 (see also the set_mode doc string).

        Positional arguments:
            marker_type: str || 'patch', 'point', 'tick', 'patch & point', 'patch & tick', 'point & tick', 'all'
                'patch' - regular polygon of degree p for p >= 3. p < 3 gives just a point which is
                          not visible in the final plot,
                'point' - regular asterisk of degree p for p >= 3. For p = 2, the marker just
                          becomes a line, as is appropriate for a nematic,
                 'tick' - single dash used to mark where the phase field is considered to be zero
                  other - all the other allowed values for the marker_type set any combination of
                          the three basic marker sub-types.
        '''
        if marker_type.lower() not in self._marker_types:
            msg = """The possible marker types are """ + "'%s', "*(len(self._marker_types)-1) + "and '%s'."
            f = tuple([marker_type for marker_type in self._marker_types])
            raise ValueError(msg % f)

        self.marker_type = marker_type.lower()

    def set_marker_color(self,color,which='patch'):
        '''
        Sets the color for any of the three marker sub-types.

        This method will have no effect on the patch color in the modes 1 and 2 (with which='both'
        and grouping='together') as the patch color will be set to the phase field color map in
        those modes.

        Positional arguments:
            color: any Matplotlib-compatible color

        Keyword arguments:
            which: str || 'patch' | 'point' | 'tick' | (default: 'patch')
                Determines which of the marker sub-types the color should apply to.
        '''
        if which.lower() not in ["patch","point","tick"]:
            raise ValueError("""The which keyword argument can be one of 'patch', 'point' or 'tick'.""")

        self.marker_colors[which] = color

    def set_marker_size(self,size):
        '''
        Sets the size of the order parameter markers. The same size is set for all three of the
        marker sub-types at once with no option of affecting each one individually.

        By default, the marker sizes are set automatically based on the marker density, but this
        can be overwritten using this method.

        Positional arguments:
            size: float, int
                Sets the marker size.
        '''
        if (isinstance(size,int) or isinstance(size,float)) and size < 0:
            raise ValueError("""size cannot be negative.""")

        try:
            size = float(size)
        except:
            raise TypeError("""size must be a number.""")

        self.marker_size = size

    def set_marker_linewidth(self,linewidth,which='point'):
        '''
        Sets the linewidth for any of the three basic marker sub-types.

        If p = 1,2, then by default the marker linewidtsh will be set automatically based on the
        marker density, but this can be overwritten using this method.

        Positional arguments:
            linewidth: float

        Keyword arguments:
            which: str || 'patch' | 'point' | 'tick' | (default: 'point')
                Determines which of the basic marker sub-types the linewidth should apply to.
        '''
        if which.lower() not in ["patch","point","tick"]:
            raise ValueError("""The which keyword argument can be one of 'patch', 'point' or 'tick'.""")

        if (isinstance(linewidth,int) or isinstance(linewidth,float)) and linewidth < 0:
            raise ValueError("""linewidth cannot be negative.""")
        try:
            linewidth = float(linewidth)
        except:
            raise TypeError("""The linewidth must be a number.""")

        self.marker_linewidths[which] = linewidth

    def set_marker_transparency(self,alpha,which='patch'):
        '''
        Sets the transparency for any of the three basic marker sub-types. The effects of this
        method will be overwritten by the set_mode method if the mode is changed to 1 or 2 (with
        which='both' and grouping='together') from any other plotting configuration. The
        transparency can be set to any desired value by calling this method after set_mode
        (see also the set_mode doc string).

        Positional arguments:
            alpha: float
                Transparency value. Because the transparency must be a number in the interval
                [0,1], if alpha is greater than 1, the transparency will be set to 1.

        Keyword arguments:
            which: 'patch' | 'point' | 'tick' | (default: 'patch')
                Determines which of the marker sub-types the transparency should apply to.
        '''
        if which.lower() not in ["patch","point","tick"]:
            raise ValueError("""The which keyword argument must be one of 'patch', 'point' or 'tick'.""")

        try:
            alpha = float(alpha)
        except:
            raise TypeError("""alpha must be a number between 0 and 1.""")

        if alpha > 1:
            self.marker_transparencies[which] = 1
        elif alpha < 0:
            self.marker_transparencies[which] = 0
        else:
            self.marker_transparencies[which] = alpha

    def set_axes_facecolor(self,color):
        if not isinstance(color,str):
            raise TypeError("""The color keyword argument must be of type <class 'str'>.""")

        self.ax_fc = color

    def set_colormap(self,colormap):
        '''
        Sets the color map for the phase field contour plot and order parameter markers where
        relevant.

        Positional arguments:
            colormap: str, Matplotlib colormap
                The colormap can be given as a string with the name of any of the standard
                Matplotlib colormaps, or as a Matplotlib colormap object.
        '''
        # add checks for colormap
        
        self.colormap = colormap

    def set_pf_transparency(self,alpha):
        '''
        Sets the transparency of the phase field contour plot. Calling this before set_mode will
        have no effect on the phase field contour plot transparency, as the set_mode method sets
        a default value for the transparency. However, calling the method after set_mode will set
        the transparency to the desired value.

        Positional arguments:
            alpha: float
                Transparency value. Because the transparency must be a number in the interval
                [0,1], if alpha is greater than 1, the phase field transparency will be set to 1.
        '''
        try:
            alpha = float(alpha)
        except:
            raise TypeError("""alpha must be a number between 0 and 1.""")

        if alpha > 1:
            self.pf_transparency = 1
        elif alpha < 0:
            self.pf_transparency = 0
        else:
            self.pf_transparency = alpha

    def preview(self,frame=None):
        '''
        Allows the user to preview a single frame of the animation.

        Keyword arguments:
            frame: int || (default: None)
                Determines which frame of the animation to preview. If frame > nt, it will simply
                be set to nt-1.
        '''
        if self.field is None:
            raise Exception("""No data to display.""")
        elif self.x is None or self.y is None:
            raise Exception("""Cannot make a plot without a fully defined coordinate grid.""")
        else:
            self._initialize_plot()

            if frame is not None:
                if not isinstance(frame,int):
                    raise TypeError("""frame must be an integer.""")
                elif isinstance(frame,int) and frame >= self.nt:
                    frame = self.nt - 1
                self._draw_frame(frame)
            else:
                self._draw_frame(0)
        plt.show()

    def animate(self,ext='gif'):
        '''
        Makes the animation of the phase field/ order parameter time evolution and saves it to the
        same location as the script from which the method is called.

        Keyword arguments:
            ext: str || 'gif' | 'mp4 | (default: 'gif')
                Sets the output file type for the animation.
        '''

        if ext.lower() not in ['gif','mp4']:
            raise ValueError("""The ext keyword argment must be either 'gif' or 'mp4'.""")

        self._initialize_plot()

        folder_name = '_%s_frames' % datetime.datetime.now().strftime('%y%m%d_%H%M%S')
        os.mkdir('./' + folder_name)
        for i in range(self.nt):
            self._draw_frame(i)
            plt.savefig('./' + folder_name + '/frame_%d.png' % i)

        ims = []
        for i in range(self.nt):
            ims.append(iio.imread('./' + folder_name + '/frame_%d.png' % i))
        frames = np.stack(ims,axis=0)
        iio.imwrite('PAA_%s.%s' % (datetime.datetime.now().strftime('%y%m%d_%H%M%S'),ext.lower()),frames)

        shutil.rmtree('./' + folder_name)
