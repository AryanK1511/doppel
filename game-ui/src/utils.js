export function getCamScale(k) {
  const resizeFactor = k.width() / k.height();
  if (resizeFactor < 1) {
    return 1;
  } else {
    return 1.5;
  }
}

export function setCamScale(k) {
  const scale = getCamScale(k);
  k.camScale(k.vec2(scale));
}
