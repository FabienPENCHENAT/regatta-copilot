// The race course from races/<id>.json: start line of the chosen boat, gates, marks, finish,
// forbidden zones (magenta, dashed, like restricted areas on charts) and vigilance zones.

export class CourseLayer {
  #layer;

  constructor(map, translator, colors) {
    this.translator = translator;
    this.color = colors;
    this.#layer = L.layerGroup().addTo(map);
  }

  render(race, boatId) {
    this.#layer.clearLayers();
    race.exclusion_zones.forEach((zone) => this.#zone(zone, "forbidden"));
    race.vigilance_zones.forEach((zone) => this.#zone(zone, "vigilance"));
    const boat = race.boats.find((b) => b.id === boatId) ?? race.boats[0];
    this.#line(boat.start_line, "--ink", this.translator.t("course.start_line", { boat: this.translator.t(`boat.${boat.id}`) }));
    race.marks.forEach((mark) => this.#mark(mark));
    this.#line(race.finish.line, "--ink", this.translator.t("course.finish"));
  }

  #zone(zone, kind) {
    const forbidden = kind === "forbidden";
    const style = {
      pane: "course", weight: 1.5, color: this.color(forbidden ? "--restricted" : "--vigilance"),
      dashArray: forbidden ? "6 4" : "2 4", fillOpacity: forbidden ? 0.12 : 0.06,
    };
    const shape = zone.shape === "line" ? L.polyline(zone.points, style) : L.polygon(zone.points, style);
    shape.bindTooltip(this.translator.t(forbidden ? "course.forbidden_zone" : "course.vigilance_zone", { name: zone.name }));
    shape.addTo(this.#layer);
  }

  #line(points, token, label) {
    L.polyline(points, { pane: "course", color: this.color(token), weight: 4 }).bindTooltip(label).addTo(this.#layer);
    points.forEach((p) => this.#buoy(p, "--buoy-start", label));
  }

  #mark(mark) {
    const name = this.translator.t(`mark.${mark.id}`);
    if (mark.type === "gate") {
      L.polyline(mark.points, { pane: "course", color: this.color("--buoy-gate"), weight: 2, dashArray: "4 3" }).addTo(this.#layer);
      mark.points.forEach((p) => this.#buoy(p, "--buoy-gate", name));
      return;
    }
    const side = this.translator.t(`course.leave_to_${mark.leave_to}`);
    this.#buoy(mark.position, mark.leave_to === "port" ? "--buoy-port" : "--buoy-starboard", `${name} · ${side}`);
  }

  #buoy(latLng, token, label) {
    L.circleMarker(latLng, {
      pane: "course", radius: 5, weight: 2, color: this.color("--ink"), fillColor: this.color(token), fillOpacity: 1,
    }).bindTooltip(label).addTo(this.#layer);
  }
}
