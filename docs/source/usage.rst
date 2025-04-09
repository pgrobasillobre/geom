Usage
-----

Once the environment is set up, you can run the following command to see all available options:

```
geom -h
```

This will display the help menu with all the available commands and their descriptions.

Example commands:
------------------

- **Rotate geometry 90 degrees** around the Y-axis:

```
geom -r1 90 geom.xyz origin_CM_yes +y
```

- **Generate a nanoparticle sphere**:

```
geom -create -sphere Ag 30
```

- **Generate a graphene ribbon**:

```
geom -create -graphene rib 50 20
```
