import io
import os
import py3Dmol
import webbrowser
import tempfile
import matplotlib.pyplot as plt

from geom.classes import molecule, parameters
from geom.functions import output 
from rdkit import Chem
from rdkit.Chem import Draw, rdDepictor, AllChem
from rdkit.Chem.Draw import rdMolDraw2D
# -------------------------------------------------------------------------------------
def select_case(inp):
  """
    debugpgi
  """

  if (inp.rdkit_visualize): visualize(inp)
# -------------------------------------------------------------------------------------
def visualize(inp):
  """
  debugpgi
  """

  # Check input
  inp.check_input_case()   
  #general.create_results_geom()
 
  # Read geometry
  mol = load_rdkit_file(inp.rdkit_mol_file)

  # Visualize 2D or 3D
  if (inp.rdkit_visualize_2d): plot_2d_molecule(mol, inp.stereo_annotations)
  if (inp.rdkit_visualize_3d): plot_3d_molecule(mol)
# -------------------------------------------------------------------------------------
def load_rdkit_file(filename):
    """
    debugpgi
    Return a single RDKit Mol for .smi/.sdf/.mol/.pdb files.
    """
    param = parameters.parameters()
    ext = filename[-4:].lower()

    if ext == ".smi":
        # Read the first SMILES from the file
        with open(filename, "r") as f:
            line = f.readline().strip()
        smiles = line.split()[0] if line else ""
        return Chem.MolFromSmiles(smiles)

    elif ext in (".sdf", ".mol"):
        # Return the first valid molecule from the supplier
        supp = Chem.SDMolSupplier(filename, removeHs=False)
        for m in supp:
            if m is not None:
                return m
        return None  # if no valid entries

    elif ext == ".pdb":
        return Chem.MolFromPDBFile(filename, removeHs=False, sanitize=True)

    else:
        msg = (
            f"File extension '{ext}' for RDKit not supported.\n\n"
            "   Accepted file extensions:"
            + "".join(f"\n     - {extension}" for extension in param.rdkit_file_extensions)
        )
        output.error(msg)
# -------------------------------------------------------------------------------------
def plot_2d_molecule(mol, stereo_annotations, 
                     size=(800, 700), annotate_atom_indices=False, kekulize = True):
    """
    Compute 2D coords and render as an image, then show it.
    - stereo_annotations=True adds R/S and E/Z labels.
    """
    m2d = Chem.Mol(mol)  # Avoid overwritting
    rdDepictor.Compute2DCoords(m2d)
    Chem.AssignStereochemistry(m2d, cleanIt=True, force=True, flagPossibleStereoCenters=True)

    atom_labels = None
    if annotate_atom_indices:
        atom_labels = {i: str(i) for i in range(m2d.GetNumAtoms())}

    if not stereo_annotations:
        # Simple path: wedge bonds, no extra labels
        img = Draw.MolToImage(
            m2d, size=size, kekulize=True,
            atomLabels=atom_labels, wedgeBonds=True
        )
    else:
        # rdMolDraw2D path with stereo labels
        w, h = size
        drawer = rdMolDraw2D.MolDraw2DCairo(w, h)
        opts = drawer.drawOptions()
        opts.addStereoAnnotation = True
        opts.addAtomIndices = annotate_atom_indices
        opts.padding = 0.05
        if kekulize:
            try:
                Chem.Kekulize(m2d, clearAromaticFlags=True)
            except Exception:
                pass
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, m2d)
        drawer.FinishDrawing()

        png = drawer.GetDrawingText()
        import PIL.Image as Image
        img = Image.open(io.BytesIO(png))

    plt.imshow(img)
    plt.axis("off")
    plt.tight_layout()
    plt.show()
# -------------------------------------------------------------------------------------
def ensure_3d_conformer(mol):
    """
    Add Hs and embed a 3D conformer with ETKDG.
    """

    m3d = Chem.AddHs(mol)
    AllChem.EmbedMolecule(m3d, AllChem.ETKDGv3())

    return m3d
# -------------------------------------------------------------------------------------
def plot_3d_molecule(mol, style="ballstick", width=1600, height=900, background="1xFFFFFF"):
    """
    Interactive 3D using py3Dmol.
    In CLI: generates a temporary HTML file and opens it in the default browser.
    """
    # Ensure we have a 3D conformer
    m3d = ensure_3d_conformer(mol)

    mblock = Chem.MolToMolBlock(m3d)
    view = py3Dmol.view(width=width, height=height)
    view.addModel(mblock, 'mol')

    view.setStyle({'sphere': {'scale': 0.3}, 'stick': {}})

    view.setBackgroundColor(background)
    view.zoomTo()

    # Write HTML to a temp file and open in browser
    html = view._make_html()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w") as f:
        f.write(html)
        temp_html_path = f.name

    webbrowser.open("file://" + os.path.abspath(temp_html_path))
# -------------------------------------------------------------------------------------
