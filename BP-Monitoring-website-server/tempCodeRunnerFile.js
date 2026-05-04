
        const latestDoc = await ppgCollection.find().sort({ serialNumber: -1 }).limit(1).toArray();
        console.log("Backend: Latest document fetched -", latestDoc);