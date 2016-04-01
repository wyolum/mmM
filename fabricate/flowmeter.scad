// Sensiron SF3000 inlet/outlet adapter
inletID = 19.83;
couplerID = 24.75;
couplerLength = 24;
couplerEx = 50; // coupler should extend at 5-10cm
inch = 25.4;
hose_id = .125*inch;
cone_h = (couplerID+2)/2;

flow_exit_od = 22;
flow_exit_length = 23.5;
flow_od = 22.5;
flow_body_length=25;
flow_h = flow_body_length + 2 * flow_exit_length;

min_straight = 100;
coupler_length = flow_exit_length + min_straight;
module flow_meter(){
  $fn =99;
  cylinder(d1=flow_exit_od, d2=flow_od, h=flow_exit_length);
  translate([0, 0, flow_exit_length])cylinder(d=flow_od, h=flow_body_length);
  translate([0, 0, flow_exit_length + flow_body_length])cylinder(d2=flow_exit_od, d1=flow_od, h=flow_exit_length);
}

module hose_barb(){
    $fn = 99;
    difference(){
        union(){
            cylinder(d=hose_id,h = .25*inch);
            translate([0,0,.25*inch])cylinder(r1 = (hose_id/2)+.5, r2 =(hose_id/2) - .5, h = .25 *inch);
            translate([0,0,.35*inch])cylinder(r1 = (hose_id/2)+.5, r2 =(hose_id/2) - .5, h = .15 *inch);
        }
        translate([0,0,-1])cylinder(d=hose_id -1, h = 1.25 *inch);
    }
} 
module coupler(){
    $fn =99;
    cylinder(d=couplerID+2, h=coupler_length);
    translate([0, 0, coupler_length])cylinder(d1=couplerID+2, d2=hose_id+1.2, h=cone_h);
    translate([0, 0, coupler_length + cone_h])hose_barb();
}

module oring(){
  $fn=99;
  rotate_extrude(convexity = 10)
    translate([(couplerID-1)/2, 0, 0])
    circle(r = 1);
}

//hose_barb();

if(true){
  difference(){
    translate([0, 0, 0])coupler();
    translate([0, 0, -flow_h+flow_exit_length])scale([1.05, 1.05, 1])flow_meter();
    translate([0, 0, coupler_length])cylinder(d1=couplerID, d2=hose_id, h=cone_h);
    cylinder(d=inletID, h=coupler_length+1);
    translate([0, 0, 1])oring();
    cylinder(h=1000, d=hose_id-1, $fn=99);
  }
 }
//translate([0, 0, 0])coupler();
//  oring();

