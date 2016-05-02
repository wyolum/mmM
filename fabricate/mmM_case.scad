inch = 25.4;

acr_t = 3;
screen_x = 192.96;
screen_y = 110.76;
screen_r = 7.5;
screen_d = 2 * screen_r;

slant = 30;
base_y = screen_y * cos(slant);
base_x = screen_x;
h1 = 50;
h2 = h1 + screen_y * cos(slant);

rim_t = 1.2;
interior_x = 166.2 + .5;
interior_y = 101 + .5;
interior_z = rim_t + 2;
interior_off_x = 14 + 1 - .25;
interior_off_y = 3.5 - .25;

module slotted_cylinder(h){
  difference(){
    cylinder(r=screen_r, h = h);
    translate([-screen_r*.8, 0, -1])cube([acr_t, 100, h + 2]);
    translate([0, -screen_r*.8, -1])cube([100, acr_t, h + 2]);
    cylinder(h=h+2, d=2, $fn=20);
  }
}

module display(){
  difference(){
    translate([screen_r, screen_r, 0]) minkowski(){
      cube([screen_x - screen_d, screen_y - screen_d, rim_t]);
      cylinder(r=screen_r, h=rim_t);
    }
    translate([interior_off_x, interior_off_y, -.1])
      cube([interior_x, interior_y, interior_z]);
  }
}

union(){
  translate([0, sin(slant) * rim_t, h1])
    rotate(v=[1, 0, 0],a = slant) 
    display();
  
  
  difference(){
    union(){
      translate([screen_r, screen_r, 0])slotted_cylinder(h = h1 + 15);
      translate([base_x - screen_r, screen_r, 0])
	rotate(v=[0,0, 1], a=90)
	slotted_cylinder(h = h1 + 15);
      translate([screen_r, base_y - screen_r * cos(slant), 0])
	rotate(v=[0,0, 1], a=-90)
	slotted_cylinder(h = h2 + 15);
      translate([base_x - screen_r, base_y - screen_r * cos(slant), 0])
	rotate(v=[0,0, 1], a=180)
	slotted_cylinder(h = h2 + 15);
    }
    translate([0, 0, h1])rotate(a=slant, v=[1, 0, 0])cube([1000, 1000, 1000]);
    color([1, 0, 0])translate([1, 0, h1])
      rotate(a=slant, v=[1, 0, 0])
      translate([interior_off_x, interior_off_y+1, -3 * interior_z])
      cube([interior_x, interior_y, 5 * interior_z]);
    color([1, 0, 0])translate([0, 0, h1])
      rotate(a=slant, v=[1, 0, 0])
      translate([interior_off_x, interior_off_y+1, -3 * interior_z])
      cube([interior_x, interior_y, 5 * interior_z]);
  }
}





