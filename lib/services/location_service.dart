import 'dart:async';
import 'package:geolocator/geolocator.dart';

class LocationException implements Exception {
  final String message;
  LocationException(this.message);

  @override
  String toString() => message;
}

class LocationService {
  // Mirrors the website's behavior: the first GPS fix on a phone is often a
  // fast, low-accuracy network fix before the chip locks on to a much more
  // exact one, so keep listening for the best reading within a time budget
  // rather than accepting whatever arrives first. A real GPS fix - especially
  // a cold start indoors - can take well over 15s, so the budget here is
  // generous, and if nothing arrives in time we fall back to the device's
  // last known location rather than failing outright.
  static const double _goodAccuracyMeters = 30;
  static const Duration _maxWait = Duration(seconds: 35);

  static Future<Position> getBestLocation() async {
    if (!await _ensurePermission()) {
      throw LocationException(
        'Location permission denied. Please enable location access for this app in your device settings.',
      );
    }

    final completer = Completer<Position>();
    Position? best;
    StreamSubscription<Position>? subscription;
    Timer? timer;
    var finished = false;

    Future<void> finish() async {
      if (finished) return;
      finished = true;
      subscription?.cancel();
      timer?.cancel();

      if (best != null) {
        completer.complete(best);
        return;
      }

      try {
        final lastKnown = await Geolocator.getLastKnownPosition();
        if (lastKnown != null) {
          completer.complete(lastKnown);
          return;
        }
      } catch (_) {
        // Fall through to the error below.
      }

      completer.completeError(LocationException(
        'Could not get a GPS fix. Make sure location is turned on and try again outdoors or near a window.',
      ));
    }

    subscription = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.best, distanceFilter: 0),
    ).listen(
      (position) {
        if (best == null || position.accuracy < best!.accuracy) {
          best = position;
        }
        if (position.accuracy <= _goodAccuracyMeters) {
          finish();
        }
      },
      onError: (_) => finish(),
    );

    timer = Timer(_maxWait, finish);

    return completer.future;
  }

  static Future<bool> _ensurePermission() async {
    if (!await Geolocator.isLocationServiceEnabled()) return false;
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    return permission == LocationPermission.always || permission == LocationPermission.whileInUse;
  }
}
