# Queries for [Overpass-Turbo](http://overpass-turbo.eu/ "Overpass-Turbo")

```
/*
  Search for website-tags that contain facebook”
  (the area to search in is your currently visible area)
*/

[out:xml][timeout:60];
// gather results
(
  node["website"~"facebook"]({{bbox}});
  way["website"~"facebook"]({{bbox}});
  relation["website"~"facebook"]({{bbox}});
);

// print results
out meta;
>;
out meta qt;
```