inch = 25.4;

acr_t = 3;
screen_x = 192.96;
screen_y = 110.76;
screen_r = 7.5;
screen_d = 2 * screen_r;
screw_d = 2.5 * mm;

slant = 30;
base_y = screen_y * cos(slant);
base_x = screen_x;
h1 = 50;
h2 = h1 + screen_y * sin(slant);

rim_t = 1.2;
interior_x = 166.2 + .5;
interior_y = 101 + .5;
interior_z = rim_t + 2;
interior_z = rim_t + 1;
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
      cube([screen_x - screen_d, screen_y - screen_d, rim_t/2]);
      cylinder(r=screen_r, h=rim_t/2);
    }
    translate([interior_off_x, interior_off_y, -.1])
      cube([interior_x, interior_y, interior_z]);
  }
}

module main(){
  union(){
    translate([0, sin(slant) * rim_t, h1])
      rotate(v=[1, 0, 0],a = slant) 
      display();
    
    
    difference(){
      union(){
	translate([screen_r, screen_r, 0])
	  slotted_cylinder(h = h1 + 15);
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

    foot();
    translate([base_x - 2 * screen_r, 0, 0])foot();
    translate([base_x - 2 * screen_r, base_y - 2 * screen_r * cos(slant), 0])foot();
    translate([0, base_y - 2 * screen_r * cos(slant), 0])foot();
  }
  color([0, 1, 0])
    intersection(){
    scale([1, cos(slant), 100])
      translate([screen_r, screen_r, 0]) 
      difference(){
      minkowski(){
	cube([screen_x - screen_d, screen_y - screen_d, .0001]);
	cylinder(r=screen_r, h=rim_t);
      }
      minkowski(){
	cube([screen_x - screen_d, screen_y - screen_d, 1]);
	cylinder(r=screen_r - 1, h=rim_t);
      }
    }
    translate([0, 0, h1 - 3])rotate(a=slant, v=[1, 0, 0])cube([1000, 1000, 3]);
  }

}

module bottom1(){
  color([1, 0, 0])
  translate([screen_r, screen_r, - acr_t])minkowski(){
    cube([base_x - 2 * screen_r, base_y - 2 * screen_r, acr_t]);
    cylinder(r=screen_r, h=.0001);
  }
}
module foot(){
  translate([screen_r, screen_r, - 3 * acr_t])
    difference(){
    cylinder(r2=screen_r, r1 = screen_r * .75, h=2 * acr_t);
    cylinder(d=screw_d, h=1000, $fn=20);
    translate([0, 0, -1])
    cylinder(d=6, h=acr_t + 1, $fn=20);
  }
}
module bottom(){
  difference(){
    union(){
      translate([screen_r - 1 * acr_t, screen_r - 1 * acr_t, - acr_t])
	minkowski(){
	cube([base_x - 2 * screen_r + 2 * acr_t, 
	      base_y - 2 * screen_r + 2 * acr_t, 
	      acr_t/2]);
	cylinder(r=acr_t, h=acr_t/2);
      }
      translate([screen_r, screen_r, - acr_t])
	cylinder(r=screen_r, h=acr_t);
      translate([base_x - screen_r, screen_r, - acr_t])
	cylinder(r=screen_r, h=acr_t);
      translate([base_x - screen_r, base_y - screen_r * cos(slant), - acr_t])
	cylinder(r=screen_r, h=acr_t);
      translate([screen_r, base_y - screen_r * cos(slant), - acr_t])
	cylinder(r=screen_r, h=acr_t);
    }
    translate([screen_r, screen_r, - acr_t - 1])
      cylinder(d=screw_d, h=acr_t + 2);
    translate([base_x - screen_r, screen_r, - acr_t - 1])
      cylinder(d=screw_d, h=acr_t + 2);
    translate([base_x - screen_r, base_y - screen_r * cos(slant), - acr_t - 1])
      cylinder(d=screw_d, h=acr_t + 2);
    translate([screen_r, base_y - screen_r * cos(slant), - acr_t - 1])
      cylinder(d=screw_d, h=acr_t + 2);
  }
}

module side(){
  color([1, 0, 0])
    rotate(a=90, v=[0, -1, 0])
    intersection(){
    linear_extrude(height=acr_t)
      polygon(points=[[0, 0], [0, base_y], [h2, base_y], [h1, 0]]);
    translate([-100, screen_r + .5, -100])cube([200, base_y - 2 * screen_r, 200]);
  }
}

module front(){
  translate([screen_r, screen_r - acr_t, 0])cube([base_x - 2 * screen_r, acr_t, h1]);
}

module back(){
  translate([screen_r, base_y - screen_r + acr_t, 0])cube([base_x - 2 * screen_r, acr_t, h2]);
}

//main();
//translate([screen_r - acr_t, 0, 0])side();
//translate([base_x - screen_r + acr_t, 0, 0])side();
// front();
// back();

laser_cut = true;
if(laser_cut){
  projection()bottom();
  projection()translate([-10, 0, 0])rotate(a=-90, v=[0, 1, 0])side();
  projection()translate([base_x + 20, 0, 0])rotate(a=90, v=[0, 1, 0])side();
  projection()translate([0, -10, -2 * acr_t])rotate(a=90, v=[1, 0, 0])front();
  projection()translate([0, base_y + 10, base_y - acr_t])rotate(a=-90, v=[1, 0, 0])back();
 }
 else{
   main();
   translate([screen_r - acr_t, 0, 0])side();
   translate([base_x - screen_r + acr_t, 0, 0])side();
   front();
   back();
   bottom();
 }

