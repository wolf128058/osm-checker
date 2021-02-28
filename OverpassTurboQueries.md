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


```
/*
  Search for website-tags that contain websites without scheme at the beginning
*/

[out:xml][timeout:120];
// gather results
(
  node["website"~"."]["website"!~"^http.*"]({{bbox}});
  way["website"~"."]["website"!~"^http.*"]({{bbox}});
  relation["website"~"."]["website"!~"^http.*"]({{bbox}});
);

// print results
out meta;
>;
out meta qt;
```


```
/*
  Search for website-tags that contain tracking-parameters
*/
[out:xml][timeout:120];
// gather results
(
  node["website"~"[?#&](mc_id|utm_\\w+|fbclid|gclid|campaign_ref|gclsrc|dclid|WT.tsrc|wt.tsrc|zanpid|yclid|igshid)="]({{bbox}});
  way["website"~"[?#&](mc_id|utm_\\w+|fbclid|gclid|campaign_ref|gclsrc|dclid|WT.tsrc|wt.tsrc|zanpid|yclid|igshid)="]({{bbox}});
  relation["website"~"[?#&](mc_id|utm_\\w+|fbclid|gclid|campaign_ref|gclsrc|dclid|WT.tsrc|wt.tsrc|zanpid|yclid|igshid)="]({{bbox}});
);

// print results
out meta;
>;
out meta qt;
```