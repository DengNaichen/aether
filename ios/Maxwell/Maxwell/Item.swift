//
//  Item.swift
//  Maxwell
//
//  Created by Naicheng Deng on 2025-09-28.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
