import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:land_dispute_citizen/main.dart';

void main() {
  testWidgets('App boots to the splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(const LandDisputeCitizenApp());
    expect(find.text('Land Dispute'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });
}
