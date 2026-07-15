import 'dart:async';
import 'package:geolocator/geolocator.dart';

class LocationException implements Exception {
  final String message;
  LocationException(this.message);

  @override
  String toString() => message;
}

class LocationService {
  // The first GPS fix on a phone is often a fast, low-accuracy network fix
  // before the chip locks on to a much more exact one. Rather than making
  // the citizen stare at a blank map until a near-perfect fix arrives, every
  // fix is handed to [onUpdate] as it comes in so the pin appears and
  // refines itself immediately, while a shorter time budget than a full GPS
  // cold start still bounds how long "final" resolution takes before
  // falling back to the device's last known location.
  static const double _goodAccuracyMeters = 50;
  static const Duration _maxWait = Duration(seconds: 15);

  /// Returns the device's cached last-known position, if any, without
  /// waiting for a fresh GPS fix. Used to show a location immediately while
  /// [getBestLocation] keeps refining in the background, instead of leaving
  /// the screen blank until a full fix comes in.
  static Future<Position?> getLastKnownLocation() async {
    if (!await _ensurePermission()) return null;
    try {
      return await Geolocator.getLastKnownPosition();
    } catch (_) {
      return null;
    }
  }

  /// Resolves the best fix obtained within the time budget. If [onUpdate] is
  /// given, it's called with every fix as it arrives (each one at least as
  /// accurate as the last) so a caller can render progress immediately
  /// instead of waiting for the final result.
  static Future<Position> getBestLocation({void Function(Position)? onUpdate}) async {
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
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, distanceFilter: 0),
    ).listen(
      (position) {
        if (best == null || position.accuracy < best!.accuracy) {
          best = position;
          onUpdate?.call(position);
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
