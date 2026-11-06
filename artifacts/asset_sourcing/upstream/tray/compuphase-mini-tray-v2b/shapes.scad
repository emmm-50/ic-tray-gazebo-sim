/* right-angle trangular prism
   length = x-axis, width = y-axis, height = z-axis
   right-angle faces aligned to x-z and y-z planes */
module prism(length, width, height) {
  polyhedron(
         points=[[0,0,0], [length,0,0], [length,0,height], [0,0,height], [0,width,height], [0,width,0]],
         faces=[[0,1,2,3],[0,3,4,5],[1,5,4,2],[0,5,1],[3,2,4]]
         );
}

/* trapezoid
   length is the long side, the short side has skew subtracted from the left and right
   length must be greater than 2 * skew */
module trapezoid(length, width, height, skew) {
  overlap = skew / 1000;
  translate([skew, 0, 0])
    mirror([1, 0, 0])
      prism(skew, width, height);
  translate([skew - overlap, 0, 0])
    cube([length - 2 * skew + 2 * overlap, width, height]);
  translate([length - skew, 0, 0])
    prism(skew, width, height);
}
