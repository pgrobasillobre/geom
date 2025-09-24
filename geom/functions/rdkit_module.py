import io, sys, os, shutil
import webbrowser, tempfile
import py3Dmol
import matplotlib.pyplot as plt

from geom.classes import parameters, molecule
from geom.functions import output 

from rdkit import Chem
from rdkit.Chem import Draw, rdDepictor, AllChem, rdDetermineBonds
from rdkit.Chem.Draw import rdMolDraw2D
# -------------------------------------------------------------------------------------
def select_case(inp):
  """
    debugpgi
  """

  if (inp.rdkit_visualize): visualize(inp)

  # Eliminate tmp folder containing xyz to pdb structure
  if (inp.rdkit_mol_file_extension==".xyz"): shutil.rmtree(inp.tmp_folder)
# -------------------------------------------------------------------------------------
def visualize(inp):
  """
  debugpgi
  """

  # Check input
  inp.check_input_case()   
  #general.create_results_geom()
 
  # Read geometry
  mol = load_rdkit_file(inp)

  # Visualize 2D or 3D
  if (inp.rdkit_visualize_2d): plot_2d_molecule(mol, inp)
  if (inp.rdkit_visualize_3d): plot_3d_molecule(mol)
# -------------------------------------------------------------------------------------
def load_rdkit_file(inp):
    """
    debugpgi
    Return a single RDKit Mol for .smi/.sdf/.mol/.pdb files.
    """
    param = parameters.parameters()

    filename = inp.rdkit_mol_file
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
    
    elif ext == ".xyz":
        xyz_to_pdb(inp)
        filename = inp.rdkit_mol_file # It has been changed within xyz_to_pdb
        return Chem.MolFromPDBFile(filename, removeHs=False, sanitize=True)

    else:
        msg = (
            f"File extension '{ext}' for RDKit not supported.\n\n"
            "   Accepted file extensions:"
            + "".join(f"\n     - {extension}" for extension in param.rdkit_file_extensions)
        )
        output.error(msg)
# -------------------------------------------------------------------------------------
def plot_2d_molecule(mol, inp, size=(800, 700)):
    """
    Compute 2D coords and render as an image, then show it.
    - stereo_annotations: R/S and E/Z labels
    - annotate_atom_indices: overlays atom indices (does not replace element symbols)
    """
    stereo_annotations = inp.stereo_annotations
    annotate_atom_indices = inp.atom_index
    black_and_white = inp.rdkit_bw

    m2d = Chem.Mol(mol)  # Avoid overwriting original
    rdDepictor.Compute2DCoords(m2d)
    Chem.AssignStereochemistry(m2d, cleanIt=True, force=True, flagPossibleStereoCenters=True)

    # rdMolDraw2D: labels for stereo + atom indices
    w, h = size
    drawer = rdMolDraw2D.MolDraw2DCairo(w, h)
    opts = drawer.drawOptions()
    opts.addStereoAnnotation = bool(stereo_annotations)
    opts.addAtomIndices = bool(annotate_atom_indices)
    
    if black_and_white: opts.useBWAtomPalette()

    opts.padding = 0.05

    # Kekulize for nicer aromatic display (ignore failures)
    try:
        Chem.Kekulize(m2d, clearAromaticFlags=True)
    except Exception:
        pass

    rdMolDraw2D.PrepareAndDrawMolecule(drawer, m2d)
    drawer.FinishDrawing()

    png = drawer.GetDrawingText()
    import PIL.Image as Image, io
    img = Image.open(io.BytesIO(png))

    plt.imshow(img)
    plt.axis("off")
    plt.tight_layout()
    plt.show()
# -------------------------------------------------------------------------------------
def plot_3d_molecule(mol, style="ballstick", width=1600, height=900, background="1xFFFFFF"):
    """
    Interactive 3D using py3Dmol.
    In CLI: generates a temporary HTML file and opens it in the default browser.
    """
    # Ensure we have a 3D conformer. Add Hs and embed a 3D conformer with ETKDG.
    m3d = Chem.AddHs(mol)
    AllChem.EmbedMolecule(m3d, AllChem.ETKDGv3())

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
def xyz_to_pdb(inp):
    """
    Convert XYZ -> PDB .
    Steps:
      1) Read XYZ with ASE (symbols + 3D coords)
      2) Build an RDKit mol with those atoms/coords
      3) Infer bonds from geometry (DetermineBonds)
      4) Sanitize and assign stereochemistry (R/S, E/Z)
      5) Write PDB with CONECT records

    Returns:
      inp with inp.rdkit_mol_file pointing to the generated PDB.
    """

    # Determine the script's location
    script_path = os.path.abspath(__file__)
    script_dir  = os.path.dirname(script_path)
    base_dir    = os.path.dirname(script_dir)

    # Create tmp folder
    inp.tmp_folder = os.path.join(base_dir, 'tmp')
    if os.path.exists(inp.tmp_folder):
        shutil.rmtree(inp.tmp_folder)
    os.mkdir(inp.tmp_folder)

    # --- 1) Read XYZ ---
    tmp_mol = molecule.molecule()
    tmp_mol.read_geom(inp.rdkit_mol_file,False)

    symbols = tmp_mol.atoms
    coords   = tmp_mol.xyz.T      # (N, 3) in Å

    # --- 2) Build an RDKit molecule with those atoms & coordinates ---
    rw = Chem.RWMol()
    for sym in symbols:
        rw.AddAtom(Chem.Atom(sym))
    mol = rw.GetMol()

    conf = Chem.Conformer(len(symbols))
    for i, (x, y, z) in enumerate(coords):
        conf.SetAtomPosition(i, (float(x), float(y), float(z)))
    mol.AddConformer(conf, assignId=True)

    # --- 3) Infer bonds from 3D geometry (since XYZ has none) ---
    # Adds bonds (and proposes bond orders) by comparing inter-atomic distances to element-specific covalent radii and common valence patterns.
    rdDetermineBonds.DetermineBonds(mol)

    # --- 4) Sanitize & assign stereochemistry from structure ---
    
    # Makes the graph chemically consistent so stereo perception won’t fail:
    #    - checks valences, assigns formal charges, sets implicit H counts,
    #    - perceives aromaticity/kekulization, normalizes bond types, etc.

    Chem.SanitizeMol(mol)

    # Assign tetrahedral chirality from 3D and E/Z on double bonds

    # Tag potential tetrahedral centers as clockwise/counterclockwise
    Chem.rdmolops.AssignAtomChiralTagsFromStructure(mol)

    # Converts those tags into CIP R/S assignments and/or E/Z (cis/trans) to double bonds 
    Chem.AssignStereochemistry(mol, cleanIt=True, force=True) # cleanIt=True: Before assigning new stereo info, RDKit clears any old/stale stereo flags that might already be present in the molecule. 
                                                              # force = True: Recomputes even if something was set

    # --- 5) Write PDB with CONNECT records ---
    pdb_out = os.path.join(inp.tmp_folder, os.path.splitext(os.path.basename(inp.rdkit_mol_file))[0] + ".pdb")
    Chem.MolToPDBFile(mol, pdb_out)

    # Update the input object to point to the new PDB
    inp.rdkit_mol_file = pdb_out
    return inp
# -------------------------------------------------------------------------------------
