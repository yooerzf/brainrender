from bg_atlasapi.bg_atlas import BrainGlobeAtlas
from vedo import Plane
import numpy as np

from brainrender import settings
from .actor import Actor
from ._io import load_mesh_from_file
from ._utils import return_list_smart


class Atlas(BrainGlobeAtlas):
    def __init__(self, atlas_name=None):
        atlas_name = atlas_name or settings.DEFAULT_ATLAS
        BrainGlobeAtlas.__init__(
            self, atlas_name=atlas_name, print_authors=False
        )

    def get(self, _type, *args, **kwargs):
        # returns Region, Neuron, Streamlines... instances
        if _type == "region":
            return self._get_region(*args, **kwargs)
        else:
            raise ValueError(f"Unrecognized argument {_type}")

    def _get_region(self, *regions, alpha=1, color=None):
        if not regions:
            return None

        actors = []
        for region in regions:
            if region not in self.lookup_df.acronym.values:
                print(
                    f"The region {region} doesn't seem to belong to the atlas being used: {self.atlas_name}. Skipping"
                )
                continue

            # Get mesh
            obj_file = str(self.meshfile_from_structure(region))
            mesh = load_mesh_from_file(obj_file, color=color, alpha=alpha)

            # Get color
            if color is None:
                color = [
                    x / 255
                    for x in self._get_from_structure(region, "rgb_triplet")
                ]

            actor = Actor(mesh, name=region, br_class="brain region")
            actor.c(color).alpha(alpha)
            actors.append(actor)

        return return_list_smart(actors)

    def get_plane(
        self,
        pos=None,
        norm=None,
        plane=None,
        sx=None,
        sy=None,
        color="lightgray",
        alpha=0.25,
        **kwargs,
    ):
        """ 
            Returns a plane going through a point at pos, oriented 
            orthogonally to the vector norm and of width and height
            sx, sy. 

            :param pos: 3-tuple or list with x,y,z, coords of point the plane goes through
            :param norm: 3-tuple with plane's normal vector (optional)
            :param sx, sy: int, width and height of the plane
            :param plane: "sagittal", "horizontal", or "frontal"
            :param color, alpha: plane color and transparency
        """
        axes_pairs = dict(sagittal=(0, 1), horizontal=(2, 0), frontal=(2, 1))

        pos = pos or self.root.centerOfMass()
        try:
            norm = norm or self.space.plane_normals[plane]
        except KeyError:
            raise ValueError(
                f"Could not find normals for plane {plane}. Atlas space provides these normals: {self.space.plane_normals}"
            )

            # Get plane width and height
        idx_pair = (
            axes_pairs[plane]
            if plane is not None
            else axes_pairs["horizontal"]
        )

        bounds = self.root.bounds()
        root_bounds = [
            [bounds[0], bounds[1]],
            [bounds[2], bounds[3]],
            [bounds[4], bounds[5]],
        ]

        wh = [float(np.diff(root_bounds[i])) for i in idx_pair]
        if sx is None:
            sx = wh[0]
        if sy is None:
            sy = wh[1]

        # return plane
        return Actor(
            Plane(pos=pos, normal=norm, sx=sx, sy=sy, c=color, alpha=alpha),
            name=f"Plane at {pos} norm: {norm}",
            br_class="plane",
        )