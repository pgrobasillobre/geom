import io, sys, os, shutil
import webbrowser, tempfile
import py3Dmol
import matplotlib.pyplot as plt

from geom.classes import parameters, molecule
from geom.functions import output 

from rdkit import Chem
from rdkit.Chem import Draw, rdDepictor, AllChem, rdDetermineBonds, rdAbbreviations
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

        if (inp.remove_H):
            mol = Chem.RemoveHs(Chem.MolFromSmiles(smiles))
        else:
            mol = Chem.MolFromSmiles(smiles)

        return mol

    elif ext in (".sdf", ".mol"):
        # Return the first valid molecule from the supplier
        supp = Chem.SDMolSupplier(filename, removeHs=inp.remove_H)
        for m in supp:
            if m is not None:
                return m
        return None  # if no valid entries

    elif ext == ".pdb":
        return Chem.MolFromPDBFile(filename, removeHs=inp.remove_H, sanitize=True)
    
    elif ext == ".xyz":
        xyz_to_pdb(inp)
        filename = inp.rdkit_mol_file # It has been changed within xyz_to_pdb
        return Chem.MolFromPDBFile(filename, removeHs=inp.remove_H, sanitize=True)

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

    legend_text = ""

    hl_atoms = hl_bonds = hatom = hbond = None

    m2d = Chem.Mol(mol)  # Avoid overwriting original
    rdDepictor.Compute2DCoords(m2d)
    Chem.AssignStereochemistry(m2d, cleanIt=True, force=True, flagPossibleStereoCenters=True)
    
    # --- Substructure match ---
    if inp.rdkit_match:
        ra, rb, rac, rbc = match_substructure(m2d, inp.match_smiles)  # your function (returns atoms/bonds + color maps)
        hl_atoms, hl_bonds, hatom, hbond = _merge_highlights(hl_atoms, hl_bonds, hatom, hbond, ra, rb, rac, rbc)

    # --- Aromaticity ---
    if inp.check_aromaticity:
        aa, ab, aac, abc = find_aromatic_highlights(m2d)  
        hl_atoms, hl_bonds, hatom, hbond = _merge_highlights(hl_atoms, hl_bonds, hatom, hbond, aa, ab, aac, abc)

    # --- Abbreviations ---
    if inp.rdkit_abbreviations:
        abbrevs = rdAbbreviations.GetDefaultAbbreviations()
        m2d = rdAbbreviations.CondenseMolAbbreviations(m2d, abbrevs, maxCoverage=0.8)

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

    rdMolDraw2D.PrepareAndDrawMolecule(
        drawer, m2d,
        highlightAtoms=hl_atoms,
        highlightBonds=hl_bonds,
        highlightAtomColors=hatom,
        highlightBondColors=hbond,
        legend=legend_text
    )

    drawer.FinishDrawing()

    png = drawer.GetDrawingText()
    import PIL.Image as Image, io
    img = Image.open(io.BytesIO(png))

    # --- Pretty gnuplot-like legend to distinguish aromatic atoms/bond and matched structure ---
    if inp.check_aromaticity and inp.rdkit_match:
        
        pale_green = (153, 230, 153)  # ~ (0.6, 1.0, 0.6)
        pale_blue  = (153, 204, 255)  # ~ (0.6, 0.8, 1.0)

        entries = [
            ("Aromaticity", pale_green),
            (f'SMILES match: {getattr(inp, "match_smiles", "") or ""}'.strip(), pale_blue),
        ]
        img = _draw_gnuplot_legend_pillow(
            img,
            entries,
            corner="top_left",     
            box_alpha=190,            
            pad=14,
            swatch_size=(28, 28),
            row_gap=12,
        )

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
def match_substructure(mol, pattern):
    """
    patterns: 
        str (SMARTS/SMILES). 
    Returns:
        highlightAtoms, highlightBonds, highlightAtomColors, highlightBondColors
    """

    atom_ids, bond_ids = set(), set()

    """Try SMARTS first (for things like [CH2][OH1]); fall back to SMILES."""
    q = Chem.MolFromSmarts(pattern)
    if q is None: q = Chem.MolFromSmiles(pattern)

    if q is None: output.error(f'in substructure match cannot parse query: {pattern}')
    for m in mol.GetSubstructMatches(q, useChirality=True):
        atom_ids.update(m)
        # map query bonds to target bonds
        for qb in q.GetBonds():
            a1 = m[qb.GetBeginAtomIdx()]
            a2 = m[qb.GetEndAtomIdx()]
            b = mol.GetBondBetweenAtoms(a1, a2)
            if b is not None:
                bond_ids.add(b.GetIdx())

    if not atom_ids and not bond_ids:
        return None, None, None, None


    pale_blue = (0.6, 0.8, 1.0)
    hatom = {i: pale_blue for i in atom_ids}
    hbond = {i: pale_blue for i in bond_ids}

    return sorted(atom_ids), sorted(bond_ids), hatom, hbond
# -------------------------------------------------------------------------------------
def _merge_highlights(a_atoms, a_bonds, a_atomCols, a_bondCols,
                      b_atoms, b_bonds, b_atomCols, b_bondCols):
    """Union of two highlight sets; later colors override earlier on overlap."""
    if a_atoms is None: a_atoms, a_bonds, a_atomCols, a_bondCols = [], [], {}, {}
    if b_atoms is None: b_atoms, b_bonds, b_atomCols, b_bondCols = [], [], {}, {}
    atoms = sorted(set(a_atoms) | set(b_atoms))
    bonds = sorted(set(a_bonds) | set(b_bonds))
    atomCols = {**a_atomCols, **b_atomCols}
    bondCols = {**a_bondCols, **b_bondCols}
    return atoms or None, bonds or None, atomCols or None, bondCols or None
# -------------------------------------------------------------------------------------
def find_aromatic_highlights(m):
    """Return atom/bond ids and pale-blue color maps for aromatic atoms/bonds."""
    arom_atoms = [a.GetIdx() for a in m.GetAtoms() if a.GetIsAromatic()]
    arom_bonds = [b.GetIdx() for b in m.GetBonds() if b.GetIsAromatic()]
    
    if not arom_atoms and not arom_bonds:
        return None, None, None, None
    
    pale_green = (0.6, 1.0, 0.6)
    hatom = {i: pale_green for i in arom_atoms}
    hbond = {i: pale_green for i in arom_bonds}
    
    return arom_atoms, arom_bonds, hatom, hbond
# -------------------------------------------------------------------------------------
def _draw_gnuplot_legend_pillow(
    img,  # PIL.Image
    entries,  # list of (label:str, rgb_tuple)
    corner="bottom_right",
    box_alpha=180,
    pad=14,
    swatch_size=(28, 28),
    row_gap=12,
    font_name_candidates=("Times New Roman", "Times.ttf", "Times", "DejaVuSerif.ttf")
):
    """
    Draw a gnuplot-like legend onto a PIL image.
    entries: [("Aromaticity", (153, 230, 153)), ("SMILES match", (153, 204, 255))]
    """
    from PIL import ImageDraw, ImageFont, Image

    draw = ImageDraw.Draw(img, "RGBA")

    # Pick a font size relative to image height
    H = img.height
    base_pt = max(12, int(H * 0.04)) 
    font = None
    for name in font_name_candidates:
        try:
            font = ImageFont.truetype(name, base_pt)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Measure legend block
    text_w = 0
    text_h_total = 0
    sw, sh = swatch_size
    for label, _ in entries:
        tw, th = draw.textbbox((0, 0), label, font=font)[2:]
        text_w = max(text_w, tw)
        text_h_total += max(th, sh)

    # Total size with padding, swatch + gap
    label_gap = 10
    row_h = max(sh, int(base_pt * 1.1))
    height = pad*2 + len(entries)*row_h + (len(entries)-1)*row_gap
    width = pad*2 + sw + label_gap + text_w

    # Position box
    inset = 18
    if corner == "bottom_right":
        x0 = img.width - width - inset
        y0 = img.height - height - inset
    elif corner == "bottom_left":
        x0 = inset
        y0 = img.height - height - inset
    elif corner == "top_right":
        x0 = img.width - width - inset
        y0 = inset
    else:  # top_left
        x0 = inset
        y0 = inset

    # Background (semi-transparent) + border
    box_bg = (245, 245, 245, box_alpha)  # light gray, semi-transparent
    box_border = (100, 100, 100, 255)
    draw.rounded_rectangle(
        [x0, y0, x0+width, y0+height],
        radius=10,
        fill=box_bg,
        outline=box_border,
        width=1
    )

    # Draw rows: swatch + label
    y = y0 + pad
    for label, rgb in entries:
        # swatch
        sx0, sy0 = x0 + pad, y + (row_h - sh)//2
        sx1, sy1 = sx0 + sw, sy0 + sh
        draw.rectangle([sx0, sy0, sx1, sy1], fill=rgb+(255,), outline=(60, 60, 60, 255))
        # label
        tx = sx1 + label_gap
        ty = y + (row_h - base_pt)//2 - 2
        draw.text((tx, ty), label, fill=(0, 0, 0, 255), font=font)
        y += row_h + row_gap

    return img
# -------------------------------------------------------------------------------------
